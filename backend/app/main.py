from fastapi import FastAPI

app = FastAPI() # make instance

# get method
@app.get("/")
def root():
    return{"hello":"world"}