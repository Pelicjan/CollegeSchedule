# CollegeSchedule
Python desktop application that allows you to view Military University of Technology schedule and save notes.
The application logs in to the [e-Dziekanat](https://s1.wcy.wat.edu.pl/ed1/) website using the data from the login_credentials.py file. This file should be in the main application folder.

Sample login_credentials.py file:
```
login = 'MyLogin'
password = 'MyPassword'
```

CollegeSchedule uses:
- [Qt (PySide6)](https://www.qt.io/blog/qt-for-python-6-released)
- [qt_material](https://pypi.org/project/qt-material/)
- [requests](https://pypi.org/project/requests/)
- [roman](https://pypi.org/project/roman/)

### Screenshots
##### Application window right after run
![Application window](https://i.imgur.com/O4k2gUG.png)
##### Block with saved note selected
![Block with note selected](https://i.imgur.com/klIiFUA.png)
