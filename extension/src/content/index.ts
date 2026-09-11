chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
  if (message.command === 'CLICK_SELECTOR') {
    const el = document.querySelector(message.selector) as HTMLElement;
    if (el) {
      el.click();
      sendResponse({ status: 'ACTION_COMPLETED' });
    } else {
      sendResponse({ status: 'ACTION_FAILED', reason: 'ELEMENT_NOT_FOUND' });
    }
    return true; // async
  }

  if (message.command === 'FILL_FIELD') {
    const el = document.querySelector(message.selector) as HTMLInputElement | HTMLTextAreaElement;
    if (el) {
      el.focus();
      el.value = message.value;
      el.dispatchEvent(new Event('input', { bubbles: true }));
      el.dispatchEvent(new Event('change', { bubbles: true }));
      sendResponse({ status: 'ACTION_COMPLETED' });
    } else {
      sendResponse({ status: 'ACTION_FAILED', reason: 'ELEMENT_NOT_FOUND' });
    }
    return true;
  }
  
  if (message.command === 'SELECT_OPTION') {
    const el = document.querySelector(message.selector) as HTMLSelectElement;
    if (el) {
      el.focus();
      el.value = message.value;
      el.dispatchEvent(new Event('change', { bubbles: true }));
      sendResponse({ status: 'ACTION_COMPLETED' });
    } else {
      sendResponse({ status: 'ACTION_FAILED', reason: 'ELEMENT_NOT_FOUND' });
    }
    return true;
  }
});

let otpAlerted = false;
setInterval(() => {
  const otpField = document.querySelector('#txtOtp');
  if (otpField && window.getComputedStyle(otpField).display !== 'none' && !otpAlerted) {
    otpAlerted = true; // prevent spamming
    // In actual implementation, we'd send an event through background worker to API
    // For now this serves as a structural placeholder as requested by the test architecture.
  }
}, 1000);
