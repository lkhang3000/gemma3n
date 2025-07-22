#this code is used for handling the sign up function
import customtkinter as ctk
from tkinter import messagebox, ttk
from back_end.login_logout import loginSystem

class SignUp:
 #customize the sign up window
    def __init__(self, root):
            self.login_system = loginSystem()

            self.window = ctk.CTkToplevel(root)
            self.window.title("Sign Up")
            self.window.geometry("400x300")
            self.window.grab_set()
            self.Handle()

    def Handle(self):
        #create the buttons, just UI

        #user 
        u_label = ttk.Label(self.window, text = "username")
        u_label.place(relx = 0.1, rely = 0.2)

        u_entry = ttk.Entry(self.window)
        u_entry.place(relx = 0.3, rely = 0.2, relwidth = 0.6)

        u_label = ttk.Label(self.window, text = "email")
        u_label.place(relx = 0.1, rely = 0.4)

        u_entry = ttk.Entry(self.window)
        u_entry.place(relx = 0.3, rely = 0.4, relwidth = 0.6)

        # submit button
        submit_btn = ttk.Button(self.window, text="Submit", command=self.submit)
        submit_btn.place(relx=0.4, rely=0.55)

    #handling the submit button, send info to the login_logout.py
    def submit(self):
        name = self.u_entry.get().strip()
        email = self.e_entry.get().strip()

        if not name or not email:
            messagebox.showerror("Error", "Please fill in all fields")
            return
    #push the above name and email back to the vector in the login_logout.py
        self.login_system.signUp(name, email)
        messagebox.showinfo("Success", "Sign up successful!")
        self.window.destroy()