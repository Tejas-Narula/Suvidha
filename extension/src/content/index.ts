chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
  if (message.command === 'EXECUTE_FORM_FILL') {
    const { fields, submission_config } = message;

    let missingField = null;
    let otpRequired = false;

    // Iterate through all fields from the vector schema
    for (const field of fields) {
      if (!field.selector) continue;

      const el = document.querySelector(field.selector) as HTMLElement;
      
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
          inputEl.value = field.value;
          inputEl.dispatchEvent(new Event('input', { bubbles: true }));
          inputEl.dispatchEvent(new Event('change', { bubbles: true }));
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
