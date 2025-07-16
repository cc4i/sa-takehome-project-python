import os
import json
import stripe

from dotenv import load_dotenv
from flask import Flask, request, render_template, send_from_directory, jsonify

load_dotenv()

# Config for Stripe
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')
stripe.api_version = '2025-06-30.basil'

app = Flask(__name__,
  static_url_path='',
  template_folder=os.path.join(os.path.dirname(os.path.abspath(__file__)), "views"),
  static_folder=os.path.join(os.path.dirname(os.path.abspath(__file__)), "public"))



# Config route
@app.route('/config', methods=['GET'])
def config():
  return jsonify({
    'publishableKey': os.getenv('STRIPE_PUBLISHABLE_KEY')
  })

# Home route
@app.route('/', methods=['GET'])
def index():
  return render_template('index.html')

# Favicon route
@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'public'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')

# Checkout route
@app.route('/checkout', methods=['GET'])
def checkout():
  # Just hardcoding amounts here to avoid using a database
  item = request.args.get('item')
  title = None
  amount = None
  error = None

  if item == '1':
    title = 'The Art of Doing Science and Engineering'
    amount = 2300
  elif item == '2':
    title = 'The Making of Prince of Persia: Journals 1985-1993'
    amount = 2500
  elif item == '3':
    title = 'Working in Public: The Making and Maintenance of Open Source'
    amount = 2800
  else:
    # Included in layout view, feel free to assign error
    error = 'No item selected'
  
  return render_template('checkout.html', item=item, title=title, amount=amount, error=error)

# Create payment intent route
@app.route('/create-payment-intent', methods=['POST'])
def create_payment_intent():
  # TODO: check if it's best way to get the amount
  data = request.json
  amount = data.get('amount')
  currency = data.get('currency')

  intent = stripe.PaymentIntent.create(
    amount=amount,
    currency=currency,
    automatic_payment_methods={
      'enabled': True,
      },
    )
  return jsonify(clientSecret=intent.client_secret)


# Success route
@app.route('/complete', methods=['GET'])
def complete():
  item = request.args.get('item')
  paymentIntentId = request.args.get('payment_intent')
  return render_template('complete.html', item=item, payment_intent=paymentIntentId)


# Cancel payment intent route
@app.route('/cancel_payment_intent', methods=['GET'])
def cancel_payment_intent():
  paymentIntentId = request.args.get('payment_intent')
  paymentIntent = stripe.PaymentIntent.cancel(paymentIntentId)
  return jsonify(paymentIntent=paymentIntent)

@app.route('/json_payment_intent', methods=['GET'])
def json_payment_intent():
  paymentIntentId = request.args.get('payment_intent')
  paymentIntent = stripe.PaymentIntent.retrieve(paymentIntentId)
  return jsonify(paymentIntent=paymentIntent)

# Webhook route
@app.route('/webhook', methods=['POST'])
def webhook_received():
    # You can use webhooks to receive information about asynchronous payment events.
    # For more about our webhook events check out https://stripe.com/docs/webhooks.
    webhook_secret = os.getenv('STRIPE_WEBHOOK_SECRET')
    request_data = json.loads(request.data)

    if webhook_secret:
        # Retrieve the event by verifying the signature using the raw body and secret if webhook signing is configured.
        signature = request.headers.get('stripe-signature')
        try:
            event = stripe.Webhook.construct_event(
                payload=request.data, sig_header=signature, secret=webhook_secret)
            data = event['data']
        except Exception as e:
            return e
        # Get the type of webhook event sent - used to check the status of PaymentIntents.
        event_type = event['type']
    else:
        data = request_data['data']
        event_type = request_data['type']
    data_object = data['object']

    if event_type == 'payment_intent.succeeded':
        print('💰 Payment received!')
        # Fulfill any orders, e-mail receipts, etc
        # To cancel the payment you will need to issue a Refund (https://stripe.com/docs/api/refunds)
    elif event_type == 'payment_intent.payment_failed':
        print('❌ Payment failed.')
    return jsonify({'status': 'success'})


@app.errorhandler(Exception)
def handle_exception(e):
    # Log the error for debugging
    app.logger.error(f"An error occurred: {e}")
    # Return a JSON response with a generic error message
    return jsonify(error={"message": "An internal server error occurred." + str(e)}), 500


if __name__ == '__main__':
  app.run(port=5000, host='0.0.0.0', debug=True)