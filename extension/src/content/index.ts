chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
  if (message.command === 'EXECUTE_FORM_FILL') {
    const { fields, submission_config } = message;

    let missingField = null;
    let otpRequired = false;

    // Iterate through all fields from the vector schema
    for (const field of fields) {
      if (!field.selector) continue;

      const elements = document.querySelectorAll(field.selector);
      let el: HTMLElement | null = null;
      
      // Find the first visible element
      for (let i = 0; i < elements.length; i++) {
        const current = elements[i] as HTMLElement;
        if (current.offsetWidth > 0 && current.offsetHeight > 0) {
          el = current;
          break;
        }
      }
      
      // Fallback to the first hidden element if no visible ones exist (e.g. they are rendered but CSS hidden, and we must check them)
      if (!el && elements.length > 0) {
        el = elements[0] as HTMLElement;
      }
      
      // If the element doesn't exist on the page yet, skip it
      if (!el) continue;
      
      // Check if it's required but empty
      if (field.is_required && !field.value) {
        const isOtpField = field.field_name.toLowerCase().includes('otp') || field.selector.toLowerCase().includes('otp') || field.input_type === 'otp';
        
        if (isOtpField) {
          otpRequired = true;
          // Optionally click trigger button
          if (submission_config?.otp_interceptor?.otp_trigger_button) {
            const trigger = document.querySelector(submission_config.otp_interceptor.otp_trigger_button) as HTMLElement;
            if (trigger) trigger.click();
          }
        } else {
          missingField = field.field_name;
        }
        break; // Stop execution, wait for user input
      }

      // Fill the value if present
      if (el && field.value) {
        if (field.action === 'type' || field.input_type === 'text') {
          const inputEl = el as HTMLInputElement | HTMLTextAreaElement;
          inputEl.focus();
          
          // Force value update using native setters
          const nativeInputValueSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, "value")?.set;
          const nativeTextAreaValueSetter = Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype, "value")?.set;
          
          if (inputEl instanceof HTMLInputElement && nativeInputValueSetter) {
            nativeInputValueSetter.call(inputEl, field.value);
          } else if (inputEl instanceof HTMLTextAreaElement && nativeTextAreaValueSetter) {
            nativeTextAreaValueSetter.call(inputEl, field.value);
          } else {
            inputEl.value = field.value;
          }
          
          // Dispatch full spectrum of events for strict validation (jQuery/React/Angular)
          inputEl.dispatchEvent(new KeyboardEvent('keydown', { bubbles: true, key: 'a' }));
          inputEl.dispatchEvent(new KeyboardEvent('keypress', { bubbles: true, key: 'a' }));
          inputEl.dispatchEvent(new Event('input', { bubbles: true }));
          inputEl.dispatchEvent(new KeyboardEvent('keyup', { bubbles: true, key: 'a' }));
          inputEl.dispatchEvent(new Event('change', { bubbles: true }));
          inputEl.blur();
        } else if (field.action === 'select_option' || field.input_type === 'dropdown') {
          const selectEl = el as HTMLSelectElement;
          selectEl.focus();
          selectEl.value = field.value;
          selectEl.dispatchEvent(new Event('change', { bubbles: true }));
        } else if (field.action === 'click') {
          el.click();
        }
      }
    }

    if (otpRequired) {
      sendResponse({ status: 'OTP_REQUIRED' });
    } else if (missingField) {
      sendResponse({ status: 'FIELD_REQUIRED', field_name: missingField });
    } else {
      sendResponse({ status: 'READY_FOR_SUBMISSION' });
    }

    return true; // async
  }
});
