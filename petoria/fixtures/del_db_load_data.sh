[ -f "manage.py" ] || { echo "wrong directory! run this code where the manage.py is"; exit 0; }
echo manage.py detected
rm db.sqlite3
echo db.sqlite3 removed
rm -rf chat/migrations locations/migrations posts/migrations success_story/migrations users/migrations 
echo all migration directories removed

python3 manage.py makemigrations
echo executed makemigrations
python3 manage.py makemigrations chat locations posts success_story users
echo executed makemigrations '(with clarifiers)'
python3 manage.py migrate
echo executed migrate
python3 manage.py loaddata fixtures/dev_medium.json
echo execution complete!