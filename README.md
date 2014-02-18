Small library to clear HTML page and make it more readable.

Alpha version - internal API unstable.

Usage example:

```
url = "https://www.djangoproject.com/weblog/2014/feb/17/kickstarting-improved-postgresql-support-django/"
page = CleanHtml(url)
page.process()
```

Result file will be saved to "[CURRENT DIR]/data/out" directory by default.