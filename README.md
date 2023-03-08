# cs50-finance
C$50 Finance, a web app via which you can manage portfolios of stocks. Not only this tool allows you to check real stocks’ actual prices and portfolios’ values, it will also let you “buy” and “sell” stocks by querying IEX for stocks’ prices.

Before getting started, you need to register for an API key in order to be able to query IEX’s data. To do so, follow these steps:

1. Visit iexcloud.io/cloud-login#/register/.
2. Select the “Individual” account type, then enter your name, email address, and a password, and click “Create account”.
3. Once registered, scroll down to “Get started for free” and click “Select Start plan” to choose the free plan. Note that this plan only works for 30 days from the day you create your account.
4. Once you’ve confirmed your account via a confirmation email, visit https://iexcloud.io/console/tokens.
5. Copy the key that appears under the Token column (it should begin with pk_).

Setup:

1. Setup(temporary) api key (Windows) -> cmd ->  set API_KEY=<api-key>
                            (Linux)   -> terminal -> export API_KEY=value
2. flask run (in the same cmd window)  
