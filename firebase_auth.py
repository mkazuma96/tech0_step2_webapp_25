#---------------------------------------
### Firebase Authentication: ログイン関数
import requests
import streamlit as st
import os


FIREBASE_API_KEY = os.getenv("FIREBASE_API_KEY")

def firebase_login(email,password):
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={FIREBASE_API_KEY}"
    payload = {
        "email":email,
        "password":password,
        "returnSecureToken": True
    }
    response = requests.post(url,json=payload)
    return response.json()

# Firebase Authentication: 新規登録関数
def firebase_signup(email,password):
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={FIREBASE_API_KEY}"
    payload = {
        "email":email,
        "password":password,
        "returnSecureToken": True
    }
    response = requests.post(url,json=payload)
    return response.json()

#---------------------------------------