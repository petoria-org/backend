import json
import os
import tempfile
from pathlib import Path

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.apps import apps
from django.utils import timezone

from users.models import User


class Command(BaseCommand):
    help = "Load fixture JSON(s) and optionally set a common password for all users."

    DEFAULT_PASSWORD = "Password123!"

    def add_arguments(self, parser):
        parser.add_argument(
            "--fixtures",
            nargs="+",
            default=None,
            help="Fixture file paths. Defaults to BASE_DIR/fixtures/sample_seed.json",
        )
        parser.add_argument(
            "--flush",
            action="store_true",
            help="Flush the database before loading fixtures.",
        )
        parser.add_argument(
            "--password",
            default=None,
            help="Set this password for all users after loading fixtures.",
        )
        parser.add_argument(
            "--password-env",
            default="SEED_PASSWORD",
            help="Env var used if --password is not provided.",
        )
        parser.add_argument(
            "--database",
            default="default",
            help="Database alias to use.",
        )

    def handle(self, *args, **options):
        database = options["database"]
        fixtures = options["fixtures"] or [
            str(settings.BASE_DIR / "fixtures" / "sample_seed.json")
        ]

        fixture_paths = []
        for raw in fixtures:
            candidate_paths = []
            raw_path = Path(raw)
            if raw_path.is_absolute():
                candidate_paths.append(raw_path)
            else:
                candidate_paths.append(Path(raw))
                candidate_paths.append(settings.BASE_DIR / raw)

            resolved = next((p for p in candidate_paths if p.exists()), None)
            if not resolved:
                raise CommandError(f"Fixture not found: {raw}")
            fixture_paths.append(str(resolved))

        if options["flush"]:
            self.stdout.write(self.style.WARNING("Flushing database..."))
            call_command("flush", interactive=False, database=database)

        self.stdout.write(self.style.WARNING("Loading fixtures..."))
        temp_files = []
        try:
            prepared_paths = []
            for path in fixture_paths:
                prepared = self._prepare_fixture(path)
                prepared_paths.append(prepared)
                if prepared != path:
                    temp_files.append(prepared)

            call_command("loaddata", *prepared_paths, database=database)
        finally:
            for tmp in temp_files:
                try:
                    os.remove(tmp)
                except OSError:
                    pass

        password = options["password"] or os.getenv(options["password_env"]) or self.DEFAULT_PASSWORD
        if password:
            self.stdout.write(self.style.WARNING("Setting user passwords..."))
            for user in User.objects.using(database).all():
                user.set_password(password)
                user.save(update_fields=["password"], using=database)
            self.stdout.write(self.style.SUCCESS("User passwords updated."))

        self.stdout.write(self.style.SUCCESS("Fixtures loaded."))

    def _infer_auto_value(self, model_label, fields, field_name, now_iso):
        if field_name == "updated_at":
            return fields.get("created_at", now_iso)
        if field_name == "created_at":
            if "lost_time" in fields:
                return fields["lost_time"]
            if "found_time" in fields:
                return fields["found_time"]
        return now_iso

    def _prepare_fixture(self, path):
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        now_iso = timezone.now().isoformat()
        changed = False
        for item in data:
            model_label = item.get("model")
            fields = item.setdefault("fields", {})
            try:
                app_label, model_name = model_label.split(".")
                model = apps.get_model(app_label, model_name)
            except Exception:
                continue

            for field in model._meta.fields:
                if getattr(field, "auto_now", False) or getattr(field, "auto_now_add", False):
                    if not field.null and field.name not in fields:
                        fields[field.name] = self._infer_auto_value(
                            model_label, fields, field.name, now_iso
                        )
                        changed = True

        if not changed:
            return path

        tmp = tempfile.NamedTemporaryFile(
            mode="w",
            suffix=".json",
            delete=False,
            encoding="utf-8",
        )
        json.dump(data, tmp, ensure_ascii=False)
        tmp.close()
        return tmp.name
