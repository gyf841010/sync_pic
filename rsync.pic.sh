result_hf=0
result_yd=0
for i in $(seq 10); do
	#rsync -r -hiv $1 185.2.48.8::cgroom/pictures
	rsync -r -hiv $1 218.23.120.84::cgroom/pictures
	ret=$?
	if [ $ret -ne 0 ]; then
		echo "sync hf84 error,try again"
	else
		result_hf=1
		break
	fi
done;
for i in $(seq 10); do
    #rsync -r -hiv $1 185.2.48.8::cgroom/pictures
    rsync -r -hiv $1 221.204.246.202::cgroom/pictures
    ret=$?
    if [ $ret -ne 0 ]; then
        echo "sync yd218 error,try again"
    else
        result_yd=1
        break
    fi
done;
if [ $result_hf -ne 0 ] && [ $result_yd -ne 0 ]; then
	rm -Rf $1
else
	echo "同步失败！！"
    if [ $result_hf -eq 0 ]; then
	    echo "151同步至hf84失败，失败id："$1 | formail -I 'From: sync-bot<sync-bot@qiushibaike.com>' -I 'To: gongyaofei2013@qq.com' -I 'Subject: 151图片同步失败警报' | mail -t
    else
	    echo "151同步至yd218失败，失败id："$1 | formail -I 'From: sync-bot<sync-bot@qiushibaike.com>' -I 'To: gongyaofei2013@qq.com' -I 'Subject: 151图片同步失败警报' | mail -t
    fi
fi
