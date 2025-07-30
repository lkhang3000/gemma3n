from typing import List
import csv

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

    