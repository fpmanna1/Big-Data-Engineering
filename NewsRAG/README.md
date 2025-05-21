

### Installare il virtual environment:
Questa repository non contiene al suo interno il virtual environment. Tuttavia è possibile installare in modo efficiente e preciso i moduli richiesti per gli l'esecuzione degli script attraverso l'utilizzo di [Poetry](https://python-poetry.org/docs/).
Moduli e dipendenze possono essere consultati attraverso i file `pyproject.toml` e `poetry.lock`.
Navigare fino alla cartella contenente il progetto. Eseguire da terminale i seguenti comandi:
```python
poetry install
```
### Nota sulle API key
Le API key, cosi come tutte le variabili di ambiente sono contenute nel file `.env`.

### Eseguire l'applicazione
Navigare fino alla cartella contenente il progetto. Eseguire da terminale i seguenti comandi:
```python
poetry shell
streamlit run .\Home.py
```
Dopodiche verrete indirizzati ad una pagina web con cui poter interagire con il codice (hosting in locale). Nel caso si volesse accedere dall'esterno è invece necessaria la configurazione di `ngrok`.

`Home.py` è la pagina principale dell'app, contenente il chatbot e da cui è possible accedere alle precedenti conversazionio.

`analitycs_page.py` è invece la pagina dedicata ad un EDA sui contenuti presenti nei database, con la possibilità di filtrare la ricerca su diversi campi.

### Nota sui notebooks:
Al momento il codice conenuto nei notebook è slegato dall'applicazione ed è pensato per essere eseguito in modo indipendente (in particolare su piattaforme cloud come Colab e Kaggle).