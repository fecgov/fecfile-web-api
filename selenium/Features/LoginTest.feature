Feature: Login Page
Scenario: launch FECefile login page
Given User clicks on a FEC link on FEC.Gov
Then FEC file login page is launched

#Scenario: Verify committee ID or password is blank
#Given user navigates to login url
#And user enters blank committee ID or password
#When user clicks on login button 
#Then application should display alert message 

#Scenario: Verify successful login
#Given user navigates to login url
#And user enters committee ID and password
#When user clicks on login button
#Then user should login successfully

#Scenario: Verify unsuccessful login
#Given user navigates to login url
#And user enters invalid committee ID or invalid password
#When user clicks on login button
#Then application should display invalid login message

#test