(() => {
  const toastRegion = document.getElementById("toast-region");

  function showToast(message, kind = "success") {
    if (!toastRegion) return;
    const alert = document.createElement("div");
    alert.className = `alert ${kind === "error" ? "alert-error" : "alert-success"} shadow-lg`;
    alert.setAttribute("role", "status");
    const text = document.createElement("span");
    text.textContent = message;
    alert.append(text);
    toastRegion.replaceChildren(alert);
    window.setTimeout(() => alert.remove(), 2600);
  }

  async function copyText(value) {
    if (navigator.clipboard && window.isSecureContext) {
      await navigator.clipboard.writeText(value);
      return;
    }

    const temporaryInput = document.createElement("textarea");
    temporaryInput.value = value;
    temporaryInput.setAttribute("readonly", "");
    temporaryInput.style.position = "fixed";
    temporaryInput.style.opacity = "0";
    document.body.append(temporaryInput);
    temporaryInput.select();
    const copied = document.execCommand("copy");
    temporaryInput.remove();
    if (!copied) throw new Error("Copy to clipboard is unavailable in this browser.");
  }

  document.addEventListener("click", async (event) => {
    const button = event.target.closest("[data-copy], [data-copy-target]");
    if (!button) return;

    const input = button.dataset.copyTarget
      ? document.getElementById(button.dataset.copyTarget)
      : null;
    const value = input ? input.value : button.dataset.copy;
    if (!value) return;

    try {
      await copyText(value);
      showToast("Link copied to clipboard.");
    } catch (error) {
      showToast(error.message || "Could not copy the link.", "error");
    }
  });

  document.addEventListener("submit", (event) => {
    const form = event.target;
    if (form.dataset.confirm && !window.confirm(form.dataset.confirm)) {
      event.preventDefault();
      return;
    }

    const button = form.querySelector("[data-submit-label]");
    if (!button) return;
    button.disabled = true;
    button.dataset.originalLabel = button.textContent.trim();
    button.textContent = button.dataset.submitLabel;
    button.insertAdjacentHTML(
      "afterbegin",
      '<span class="loading loading-spinner loading-xs" aria-hidden="true"></span> ',
    );
  });
})();
