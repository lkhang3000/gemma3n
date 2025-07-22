from typing import List
import csv

class User:
    def __init__(self, name: str, email: str):
        self.name = name
        self.email = email
    
class loginSystem:
    def __init__(self):
        self.log: List[User] = []

    def signUp(self, name: str, email: str):
       newUser = User(name, email)
       self.log.append(newUser)
       return newUser

    