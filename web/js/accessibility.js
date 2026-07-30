export function setStatus(element, message, state = "ready") {
  element.textContent = message;
  element.dataset.state = state;
}

export function showErrors(summary, errors) {
  const list = summary.querySelector("ul");
  list.replaceChildren();
  for (const error of errors) {
    const item = document.createElement("li");
    if (error.controlId) {
      const link = document.createElement("a");
      link.href = `#${error.controlId}`;
      link.textContent = error.message;
      link.addEventListener("click", () => {
        document.getElementById(error.controlId)?.focus();
      });
      item.append(link);
    } else {
      item.textContent = error.message;
    }
    list.append(item);
  }
  summary.hidden = errors.length === 0;
  if (errors.length > 0) {
    summary.focus();
  }
}

export function clearFieldErrors(form) {
  for (const control of form.querySelectorAll("[aria-invalid='true']")) {
    control.removeAttribute("aria-invalid");
  }
}
