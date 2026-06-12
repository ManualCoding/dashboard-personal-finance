# Fix para Streamlit Cloud: ModuleNotFoundError: No module named 'plotly'

El error ocurre porque Streamlit Cloud no instaló `plotly`. En los logs solo aparece la instalación de Streamlit y sus dependencias, lo que indica que `requirements.txt` no está en la raíz del repositorio o no fue subido/commiteado correctamente.

## Estructura correcta del repositorio

```text
dashboard-personal-finance/
├── app.py
└── requirements.txt
```

## requirements.txt

```txt
streamlit>=1.32
pandas>=2.0
numpy>=1.24
plotly>=5.18
```

## Pasos

1. Renombra `app (1).py` a `app.py`.
2. Sube `requirements.txt` a la raíz del repo, no dentro de carpetas.
3. Haz commit y push a GitHub.
4. En Streamlit Cloud cambia Main file path a `app.py`.
5. En Streamlit Cloud presiona `Manage app` -> `Reboot app`.
