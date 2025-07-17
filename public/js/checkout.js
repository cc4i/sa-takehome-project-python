
let elements;
let stripe;

if (window.location.pathname === "/checkout") {
    initialize();
    document.querySelector("#payment-form").addEventListener("submit", handleSubmit);
}

// Fetches a pyamtent intent and captures the client secret
async function initialize() {
  const {publishableKey} = await fetch("/config", {
    method: "GET",
    headers: { "Content-Type": "application/json" },
  }).then(r => r.json());

  console.debug("publishableKey", publishableKey);

  const totalDue = document.getElementById("total-due").dataset.amount;
  const currency = document.getElementById("currency").dataset.currency;
  console.log("totalDue", totalDue);
  console.log("currency", currency);
  
  const {clientSecret} = await fetch("/create-payment-intent", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      amount: totalDue,
      currency: currency,
    }),
  }).then(r => r.json());

  console.debug("clientSecret", clientSecret);
  const appearance = {
    theme: 'stripe'
  };
  stripe = Stripe(publishableKey);
  elements = stripe.elements({appearance, clientSecret});
  console.log("elements", elements);

  const paymentElementOptions = {
    layout: "accordion",
  };
  const paymentElement = elements.create('payment', paymentElementOptions);
  paymentElement.mount('#payment-element');

}

// Validate email address
function validateEmail(email) {
  const re = /^(([^<>()[\]\\.,;:\s@"]+(\.[^<>()[\]\\.,;:\s@"]+)*)|(".+"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$/;
  return re.test(String(email).toLowerCase());
}

// Handle form submission
async function handleSubmit(e) {
    // Prevents the default form submission behavior (which would reload the page)
    e.preventDefault();
    setLoading(true);

    const email = document.getElementById('email').value;
    if (!validateEmail(email)) {
        showMessage("Please enter a valid email address.");
        setLoading(false);
        return;
    }

    const item = document.getElementById("total-due").dataset.item;

    const { error } = await stripe.confirmPayment({
      elements,
      confirmParams: {
        return_url: window.location.origin + '/complete?item=' + item,
        receipt_email: email,
      },
    });
  
    // This point will only be reached if there is an immediate error when
    // confirming the payment. Otherwise, your customer will be redirected to
    // your `return_url`. For some payment methods like iDEAL, your customer will
    // be redirected to an intermediate site first to authorize the payment, then
    // redirected to the `return_url`.
    if (error.type === "card_error" || error.type === "validation_error") {
      showMessage(error.message);
    } else {
      showMessage("An unexpected error occurred.");
    }
  
    setLoading(false);
  }
  
  // ------- UI helpers -------
  function showMessage(messageText) {
    const messageContainer = document.querySelector("#payment-message");
  
    messageContainer.classList.remove("hidden");
    messageContainer.textContent = messageText;
  
    setTimeout(function () {
      messageContainer.classList.add("hidden");
      messageContainer.textContent = "";
    }, 4000);
  }
  
  // Show a spinner on payment submission
  function setLoading(isLoading) {
    if (isLoading) {
      // Disable the button and show a spinner
      document.querySelector("#submit").disabled = true;
      document.querySelector("#spinner").classList.remove("hidden");
      document.querySelector("#button-text").classList.add("hidden");
    } else {
      document.querySelector("#submit").disabled = false;
      document.querySelector("#spinner").classList.add("hidden");
      document.querySelector("#button-text").classList.remove("hidden");
    }
  }