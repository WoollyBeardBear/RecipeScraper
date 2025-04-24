import unittest
from app import *
from helpers import *
from flask import Flask, render_template, session, request, redirect, flash
from flask_session import Session

class TestTests(unittest.TestCase):
    def test_runsidey(self):
        url = "https://www.halfbakedharvest.com/baked-frosted-chocolate-donuts/"
        print("RUNNING SPIDER")
        result = scrape_and_store(url)

        print(result)
        
        

if __name__ == "__main__":
    unittest.main()