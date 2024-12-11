// Function to fetch existing messages
async function fetchMessages() {
  try {
    const response = await fetch("/edu-viewer/api/chat/history", {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
      },
    });
    const messages = await response.json();

    const chatMessages = document.getElementById("chat-messages");
    chatMessages.innerHTML = ""; // Clear existing messages

    // Loop through messages and append to chat
    messages.forEach((message) => {
      const messageContainer = document.createElement("div");
      messageContainer.className =
        message.role === "user"
          ? "chat__conversation-board__message-container reversed"
          : "chat__conversation-board__message-container";

      const messagePerson = `
        <div class="chat__conversation-board__message__person">
          <div class="chat__conversation-board__message__person__avatar ${
            message.role === "user"
              ? "chat__conversation-board__message__person__avatar__person"
              : "chat__conversation-board__message__person__avatar__ai"
          }">
          </div>
          <span class="chat__conversation-board__message__person__nickname">${
            message.role === "user" ? "You" : "Gemini"
          }</span>
        </div>
      `;

      const messageContext = `
        <div class="chat__conversation-board__message__context">
          <div class="chat__conversation-board__message__bubble">
            <span>${
              message.role === "ai"
                ? marked.parse(message.message)
                : message.message
            }</span>
          </div>
        </div>
      `;

      messageContainer.innerHTML = messagePerson + messageContext;
      chatMessages.appendChild(messageContainer);
    });

    // Scroll to the bottom after loading messages
    chatMessages.scrollTop = chatMessages.scrollHeight;
  } catch (error) {
    console.error("Error fetching messages:", error);
  }
}

document.addEventListener("DOMContentLoaded", fetchMessages);

function getSelectionText() {
  let text = "";
  const activeEl = document.activeElement;
  const activeElTagName = activeEl ? activeEl.tagName.toLowerCase() : null;
  console.log(activeElTagName, "-active tag name ", activeEl);
  if (activeElTagName === "textarea") {
    // (activeElTagName === "input" &&
    //   /^(?:url)$/i.test(activeEl.type) &&
    //   // text|search|password|tel|
    //   typeof activeEl.selectionStart === "number")
    text = activeEl.value.slice(activeEl.selectionStart, activeEl.selectionEnd);
  } else if (window.getSelection) {
    text = window.getSelection().toString();
  }
  const input = document.getElementById("chat-input");

  // Prepend the new content to the existing value
  iv = input.value;
  const regex = /--- QUOTED START ---[\s\S]*?--- QUOTED END ---/g;
  input.value = input.value.replace(regex, "").trim();
  text = "--- QUOTED START ---" + "\n" + text + "\n" + "--- QUOTED END ---";
  input.value = text + "\n" + input.value;

  console.log(text, "text from getSelectedText");
  return text;
}
let selectionTimeout;
let selectedText = "";
let lastSelectedText = "";

document.onselectionchange = function () {
  clearTimeout(selectionTimeout);

  selectionTimeout = setTimeout(() => {
    const selection = window.getSelection().toString();
    if (selection.length > 0 && lastSelectedText != selection) {
      lastSelectedText = selection;
      selectedText = getSelectionText();
      document.getElementById("selected-text").value = selectedText;
    }
  }, 300);
};
// Send chat message function (no changes)
async function sendChatMessage() {
  const input = document.getElementById("chat-input");
  var message = input.value;

  if (message) {
    const chatMessages = document.getElementById("chat-messages");

    // Append user's message
    const userMessageContainer = document.createElement("div");
    userMessageContainer.className =
      "chat__conversation-board__message-container reversed";

    const userMessagePerson = `
      <div class="chat__conversation-board__message__person">
        <div class="chat__conversation-board__message__person__avatar chat__conversation-board__message__person__avatar__person">
        </div>
        <span class="chat__conversation-board__message__person__nickname">You</span>
      </div>
    `;
    const userMessageContext = `
      <div class="chat__conversation-board__message__context">
        <div class="chat__conversation-board__message__bubble">
          <span>${message}</span>
        </div>
      </div>
    `;
    userMessageContainer.innerHTML = userMessagePerson + userMessageContext;
    chatMessages.appendChild(userMessageContainer);

    input.value = "";

    try {
      const response = await fetch("/edu-viewer/api/chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ message }),
      });
      const data = await response.json();

      const aiMessageContainer = document.createElement("div");
      aiMessageContainer.className =
        "chat__conversation-board__message-container";

      const aiMessagePerson = `
        <div class="chat__conversation-board__message__person">
          <div class="chat__conversation-board__message__person__avatar chat__conversation-board__message__person__avatar__ai">
          </div>
          <span class="chat__conversation-board__message__person__nickname">Gemini</span>
        </div>
      `;
      const html = marked.parse(data.ai_response);
      const aiMessageContext = `
        <div class="chat__conversation-board__message__context">
          <div class="chat__conversation-board__message__bubble">
            <span>${html}</span>
          </div>
        </div>
      `;

      aiMessageContainer.innerHTML = aiMessagePerson + aiMessageContext;
      chatMessages.appendChild(aiMessageContainer);
    } catch (error) {
      console.error("Error sending message:", error);
      appendMessage("System", "Failed to send message.", "system");
    }

    chatMessages.scrollTop = chatMessages.scrollHeight;
  }
}

// Event listener for sending messages
const el = document.getElementById("chat-send");
if (el) {
  el.addEventListener("click", sendChatMessage);
}
