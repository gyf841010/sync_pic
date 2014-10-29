cd /home/www/qqq/current/public/system/pictures
d=$(date -d-10day +%Y-%m-%d)
id=$(echo "select id from articles where created_at > '$d' limit 1" | mysql -uroot -p5jiu4xiejirong qqq1 | awk 'BEGIN{getline}{print}')
echo $id > clear_id
#echo "select article_id from scores where created_at>'"`date -d-1days +%Y-%m-%d`"' and status!='publish' and has_picture" | mysql -uroot -p5jiu4xiejirong qqq1 | awk 'BEGIN{getline;}{print int($NF/10000)"/"$NF}' | xargs rm -Rf

ls -l | sed '1d' | grep -v clear | awk '{if(int($NF)>0 && int($NF)<int('$id')/10000)system("sh rsync.pic.sh "$NF)}'
ls -l | grep -v clear | awk '{if(int($NF)>10000)print $NF}' | xargs rm -Rf

#ls -l | grep -v clear | awk '{if($NF<int('$id')/10000)print $NF}' | xargs -i rsync -r -hiv {} 31.201.0.6::cgroom/pictures
#ls -l | grep -v clear | awk '{if($NF<int('$id')/10000)print $NF}' | xargs rm -Rf
