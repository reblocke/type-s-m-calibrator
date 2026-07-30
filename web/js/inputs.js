function parseFiniteNumber(form, name, label) {
  const control = form.elements.namedItem(name);
  const value = control.value.trim();
  if (value === "") {
    control.setAttribute("aria-invalid", "true");
    return { error: { controlId: control.id, message: `${label} is required.` } };
  }
  const parsed = Number(value);
  if (!Number.isFinite(parsed)) {
    control.setAttribute("aria-invalid", "true");
    return {
      error: { controlId: control.id, message: `${label} must be a finite number.` },
    };
  }
  return { value: parsed };
}

export function readRequest(form) {
  const first = parseFiniteNumber(form, "first_value", "First value");
  const second = parseFiniteNumber(form, "second_value", "Second value");
  const errors = [first.error, second.error].filter(Boolean);
  if (errors.length > 0) {
    return { errors, request: null };
  }
  return {
    errors: [],
    request: {
      first_value: first.value,
      second_value: second.value,
    },
  };
}
