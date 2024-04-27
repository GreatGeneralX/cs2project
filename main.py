# main.py
from flask import Flask, render_template, request, jsonify
import yfinance as yf
from datetime import datetime

app = Flask(__name__)
app.jinja_env.globals.update(zip=zip) #Add zip to global Jinja environment

# Add validate_date function here
def validate_date(date_text):
    try:
        datetime.strptime(date_text, '%Y-%m-%d')
        return True
    except ValueError:
        return False


class StockDataLeaf:
    def __init__(self, symbol, start_date, end_date):
        self.symbol = symbol
        self.start_date = start_date
        self.end_date = end_date

    def get_data(self):
        composite_data = {}
        for child in self.children:
            data = child.get_data()
            if isinstance(data, dict) and 'Error' not in data:
                composite_data[child.symbol] = data
            else:
                composite_data[child.symbol] = {'Error': 'Error retrieving data'}
        return composite_data

class StockComponent:
    def get_data(self):
        pass

class SingleStock(StockComponent):
    def __init__(self, symbol, start_date, end_date):
        self.symbol = symbol
        self.start_date = start_date
        self.end_date = end_date

    def get_data(self):
        ticker = yf.Ticker(self.symbol)
        data = ticker.history(start=self.start_date, end=self.end_date)
        # Convert data into a dictionary and pass it to the template
        data_dict = {
            'Symbol': self.symbol,
            'Data': data.reset_index().to_dict(orient='list')
        }
        return data_dict

class StockComposite(StockComponent):
    def __init__(self):
        self.children = []

    def add(self, stock_component):
        self.children.append(stock_component)

    def get_data(self):
        composite_data = {}
        for child in self.children:
            data = child.get_data()
            if 'Error' not in data:
                composite_data[child.symbol] = data
        return composite_data
    
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        try:
            # Use getlist method to retrieve multiple symbols
            symbols = request.form.getlist('symbol')  
            start_date = request.form.get('start')
            end_date = request.form.get('end')

            #  Check if data exists
            if not symbols:  
                raise ValueError('Company name not entered')
            if not start_date:
                raise ValueError('No start date entered')
            if not end_date:
                raise ValueError('No end date entered')

            # Date format validation
            if not (validate_date(start_date) and validate_date(end_date)):
                raise ValueError('The date format is incorrect, please enter the date in YYYY-MM-DD format.')

            stock_composite = StockComposite()
            for symbol in symbols:
                stock_component = SingleStock(symbol, start_date, end_date)
                stock_composite.add(stock_component)

            results = stock_composite.get_data()  # This will be the dictionary of dictionaries.
            app.logger.info('ResultsL %s', results)
            
            return render_template('return.html', portfolio_data=results)
        except Exception as e:
            app.logger.error('Error during form processing: %s', e)
            return render_template('index.html', error=str(e))
    else:
        return render_template('index.html')

# This line should come after the function definition
if __name__ == '__main__':
    app.run(debug=False, host="0.0.0.0", port=8089)#port should be changed.