Small library to clear HTML page and make it more readable.

Alpha version - internal API unstable.

Usage example:

```
url = "https://www.djangoproject.com/weblog/2014/feb/17/kickstarting-improved-postgresql-support-django/"
page = CleanHtml(url)
page.process()
```

CLI Usage
```
python cleanhtml.py https://www.djangoproject.com/weblog/2014/feb/09/django-update-2014-01-26-2014-02-08/ --savefile res.txt
python cleanhtml.py --urlfile ../data/in/links.txt
```

Result file will be saved to "[CURRENT DIR]/data/out" directory by default.