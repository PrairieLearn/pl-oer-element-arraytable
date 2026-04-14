/* eslint-env browser */
window.PLArrayInput = function (uuid) {
  const root = document
    .querySelector(`[data-table-uuid="${uuid}"]`)
    ?.closest(".a-input-block");

  if (!root) {
    console.error("Array input root not found for UUID:", uuid);
    return;
  }

  this.element = root;
  this.originalPrefills = {};
  this.element.querySelectorAll("input.form-control").forEach((input) => {
    this.originalPrefills[input.name] = input.dataset.prefill ?? "";
  });

  this.table = this.element.querySelector("table.array-input");
  this.resetContainer = this.element.querySelector(".reset-button-container");
  this.resetButton = this.element.querySelector(".reset-button");
  this.resetConfirmContainer = this.element.querySelector(
    ".reset-confirm-container"
  );
  this.resetConfirm = this.element.querySelector(".reset-confirm");
  this.resetCancel = this.element.querySelector(".reset-cancel");

  const resetContainerWidth = () => {
    if (!this.table || !this.resetContainer) {
      return;
    }
    const tableWidth = this.table.getBoundingClientRect().width;
    this.resetContainer.style.width = `${tableWidth}px`;
  };

  const balanceLayout = () => {
    const rightColumns = Array.from(
      this.element.getElementsByClassName("right-info-column")
    );
    const leftFillers = Array.from(
      this.element.getElementsByClassName("left-filler")
    );

    if (rightColumns.length !== leftFillers.length) {
      return;
    }

    rightColumns.forEach((rightColumn, index) => {
      const width = rightColumn.getBoundingClientRect().width;
      leftFillers[index].style.width = `${width}px`;
    });
  };

  const resetToPrefillValues = () => {
    this.element.querySelectorAll("input.form-control").forEach((input) => {
      const originalValue = this.originalPrefills[input.name];
      input.value = originalValue ?? "";
    });

    this.element.querySelectorAll('.badge.bg-success, .badge.bg-danger').forEach(
      (badge) => badge.remove()
    );

    this.element.querySelectorAll('.input-group-text').forEach((text) =>
      text.remove()
    );

    this.element.querySelectorAll('[data-bs-toggle="popover"]').forEach(
      (popover) => {
        popover.removeAttribute('data-bs-content');
        popover.removeAttribute('data-bs-original-title');
        popover.removeAttribute("data-content");
        popover.removeAttribute("data-original-title");
      }
    );
  };

  const initResetButton = () => {
    if (!this.resetButton || !this.resetConfirmContainer || !this.resetConfirm || !this.resetCancel) {
      console.error("Reset confirmation elements are missing for UUID:", uuid);
      return;
    }

    this.resetButton.addEventListener("click", () => {
      this.resetButton.style.display = "none";
      this.resetConfirmContainer.style.display = "flex";
      const cancelWidth = this.resetConfirm.offsetWidth;
      this.resetCancel.style.width = `${cancelWidth}px`;
      this.resetConfirm.focus();
    });

    this.resetConfirm.addEventListener("click", () => {
      this.resetConfirmContainer.style.display = "none";
      this.resetButton.style.display = "inline-flex";
      this.resetButton.focus();
      resetToPrefillValues();
    });

    this.resetCancel.addEventListener("click", () => {
      this.resetConfirmContainer.style.display = "none";
      this.resetButton.style.display = "inline-flex";
      this.resetButton.focus();
    });
  };

  if (this.resetButton) {
    initResetButton();
  }

  resetContainerWidth();
  if (this.table instanceof Element) {
    this.resetResizeObs = new ResizeObserver(resetContainerWidth);
    this.resetResizeObs.observe(this.table);
  }

  balanceLayout();
  const rightColumns = Array.from(
    this.element.getElementsByClassName("right-info-column")
  );
  if (rightColumns.length > 0) {
    this.resizeObserver = new ResizeObserver(balanceLayout);
    rightColumns.forEach((column) => this.resizeObserver.observe(column));
  }
};

// Initialize all array inputs on page load
document.addEventListener("DOMContentLoaded", function () {
  const resetButtons = document.querySelectorAll(
    ".reset-button[data-table-uuid]"
  );

  resetButtons.forEach((button) => {
    try {
      const uuid = button.getAttribute("data-table-uuid");
      if (uuid) {
        new window.PLArrayInput(uuid);
      }
    } catch (e) {
      console.error("Error initializing array input:", e);
    }
  });
});
