cd /home/www/qqq/current/public/system/pictures
d=$(date -d-1day +%Y-%m-%d)
id=$(echo "select id from articles where created_at > '$d' limit 1" | mysql -uroot -p5jiu4xiejirong qqq1 | awk 'BEGIN{getline}{print}')
last_id=`cat clear_new_id`

ls -l | sed '1d' | grep -v clear | awk '{if(int($NF)>=int('$last_id')/10000 && int($NF)<int('$id')/10000)system("sh rsync.pic_new.sh "$NF)}'
ls -l | grep -v clear | awk '{if(int($NF)>10000)print $NF}' | xargs rm -Rf

echo $id > clear_new_id
