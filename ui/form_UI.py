#this code is used for handling the sign up function
import streamlit as st
import sys
import os
from typing import List
import csv

# Add parent directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

class User:
    def __init__(self, name: str, age: str):
        self.name = name
        self.age =  age
    
class Form:
    def __init__(self):
        self.log: List[User] = []

    def signUp(self, name: str, age: str):
       newUser = User(name, age)
       self.log.append(newUser)
       return newUser

# Fallback class for demo mode  
class medical_form:
    def signUp(self, name, age):
        print(f"Demo signup: {name}, {age}")
        return {"name": name, "age": age}

BACKEND_AVAILABLE = True

class FormUI:
    #customize the sign up window
    def __init__(self):
        st.set_page_config(
            page_title="Medical Health Form",
            page_icon="📋",
            layout="centered"
        )
        
        try:
            self.login_system = Form()
        except Exception as e:
            print(f"Error initializing login system: {e}")
            self.login_system = medical_form()  # Use fallback

    def Handle(self):
        #create the buttons, just UI
        st.title("Medical Health Form")
        st.markdown("---")
        
        # Status indicator
        if not BACKEND_AVAILABLE:
            st.warning("⚠️ Running in demo mode")
        
        # Create form
        with st.form("medical_form"):
            # user name
            name = st.text_input("Full Name:", placeholder="Enter your full name")
            
            # age
            age = st.text_input("Age:", placeholder="Enter your age")
            
            # submit button
            submitted = st.form_submit_button("Submit")
            
            if submitted:
                self.submit(name, age)

    #handling the submit button, send info to the backend
    def submit(self, name, age):
        name = name.strip()
        age = age.strip()

        if not name or not age:
            st.error("Please fill in all fields")
            return
            
        # Validate age is a number
        try:
            age_int = int(age)
            if age_int < 0 or age_int > 150:
                st.error("Please enter a valid age (0-150)")
                return
        except ValueError:
            st.error("Age must be a number")
            return

        try:
            # Push the name and age back to the backend
            result = self.login_system.signUp(name, age)
            
            if BACKEND_AVAILABLE:
                st.success("Medical form submitted successfully!")
            else:
                st.success("Form submitted in demo mode!\n(Data not actually saved)")
            
        except Exception as e:
            st.error(f"Failed to submit form: {str(e)}")

# Main execution
if __name__ == "__main__":
    try:
        form_ui = FormUI()
        form_ui.Handle()
    except Exception as e:
        st.error(f"Application startup error: {str(e)}")
else:
    # When run by streamlit command
    try:
        form_ui = FormUI()
        form_ui.Handle()
    except Exception as e:
        st.error(f"Application startup error: {str(e)}")