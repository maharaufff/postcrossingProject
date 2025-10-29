const BASE_URL = "http://127.0.0.1:5000";


async function registerUser() {
  const username = document.getElementById("username").value;
  const email = document.getElementById("email").value;
  const country = document.getElementById("country").value;

  const response = await fetch(`${BASE_URL}/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, email, country })
  });

  const data = await response.json();
  alert(data.message || data.error);
}


async function sendPostcard() {
  const sender = document.getElementById("sender").value;
  const postcard_code = document.getElementById("postcard_code").value;

  const response = await fetch(`${BASE_URL}/send_postcard`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ sender, postcard_code })
  });

  const data = await response.json();
  document.getElementById("sendResult").innerText =
    data.message || data.error;
}

async function viewReceived() {
  const username = document.getElementById("receiver_username").value;

  const response = await fetch(`${BASE_URL}/received/${username}`);
  const data = await response.json();

  const list = document.getElementById("receivedList");
  list.innerHTML = "";

  if (data.length === 0) {
    list.innerHTML = "<li>No postcards received yet.</li>";
    return;
  }

  data.forEach(card => {
    const li = document.createElement("li");
    li.textContent = `${card.sender} → ${card.receiver} [${card.postcard_code}] (${card.status})`;
    list.appendChild(li);
  });
}

