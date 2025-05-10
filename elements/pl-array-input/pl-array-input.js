/* eslint-env browser */
window.PLArrayInput = function (uuid, options) {
  // make the id of the element use query selector to choose the table reset button we are looking for
  this.element = document
    .querySelector('[data-table-uuid="' + uuid + '"]')
    .closest(".a-input-block");
  // If not found, print error to console
  if (!this.element) {
    console.log("array couldn't be retreived", uuid);
  }
  // store prefill values immediately when page loads
  this.originalPrefills = {};
  this.element.querySelectorAll("input.form-control").forEach((input) => {
    this.originalPrefills[input.getAttribute("name")] = input.dataset.prefill;
  });

  // Initialize reset button functionality
  this.resetButton = this.element.querySelector(".reset-button");
  if (!this.resetButton) {
    console.error("Reset button not found for UUID:", uuid);
    return;
  }
  //derived some of this code from script-editor (restoreoriginalbutton code)
  this.resetConfirmContainer = this.element.querySelector(
    ".reset-confirm-container"
  );
  this.resetConfirm = this.element.querySelector(".reset-confirm");
  this.resetCancel = this.element.querySelector(".reset-cancel");

  if (this.resetConfirmContainer && this.resetConfirm && this.resetCancel) {
    this.initResetButton();
  } else {
    console.error("Reset confirmation elements not found for UUID:", uuid);
  }

  resetContainerWidth();
  this.table = this.element.querySelector('table.array-input');
  this.resetContainer = this.element.querySelector('.reset-button-container');
  this.resetResizeObs = new ResizeObserver(() => {
    resetContainerWidth();
  });
  this.resetResizeObs.observe(this.table);

  balanceLayout();
  // adjust left filler width every time right column's width changes
  this.rightColumn = document.getElementsByClassName('right-info-column');  
  this.resizeObserver = new ResizeObserver(() => {
    balanceLayout();
  });  
  for (let i = 0; i < this.rightColumn.length; i++) {
    this.resizeObserver.observe(this.rightColumn[i]);
  }
};

function resetContainerWidth() {
  // limit buttons to table width
  this.table = this.element.querySelector('table.array-input');
  this.resetContainer = this.element.querySelector('.reset-button-container');
  
  if (this.table && this.resetContainer) {
    this.tableWidth = this.table.getBoundingClientRect().width; 
    this.resetContainer.style.width = `${this.tableWidth}px`;
  }
}

// resize left filler column, mirroring the right div with score and help text, to center the table
function balanceLayout() {
  this.rightColumn = document.getElementsByClassName('right-info-column');
  this.leftFiller = document.getElementsByClassName('left-filler');
  // sanity test
  if (this.rightColumn.length == this.leftFiller.length) {
    for (let i = 0; i < this.rightColumn.length; i++) {
      this.currWidth = this.rightColumn[i].getBoundingClientRect().width;
      this.leftFiller[i].style.width = `${this.currWidth}px`;
    }
  }
};

//copy pasted this entire part from script editor for confirmation
window.PLArrayInput.prototype.initResetButton = function () {
  this.resetButton.addEventListener("click", () => {
    this.resetButton.style.display = "none";
    this.resetConfirmContainer.style.display = "block";
    this.cancelWidth = this.resetConfirm.offsetWidth;
    this.resetCancel.style.width = `${this.cancelWidth}px`;
    this.resetConfirm.focus();
  });

  this.resetConfirm.addEventListener("click", () => {
    this.resetConfirmContainer.style.display = "none";
    this.resetButton.style.display = "block";
    this.resetButton.focus();
    this.resetToPrefillValues();
  });

  this.resetCancel.addEventListener("click", () => {
    this.resetConfirmContainer.style.display = "none";
    this.resetButton.style.display = "block";
    this.resetButton.focus();
  });
};

window.PLArrayInput.prototype.resetToPrefillValues = function () {
  // reset input values
  this.element.querySelectorAll("input.form-control").forEach((input) => {
    const originalValue = this.originalPrefills[input.getAttribute("name")];
    input.value = originalValue || "";
  });

  this.element
    .querySelectorAll(".badge-success, .badge-danger")
    .forEach((badge) => {
      badge.parentNode.removeChild(badge);
    });

  this.element.querySelectorAll(".input-group-text").forEach((text) => {
    text.parentNode.removeChild(text);
  });

  this.element
    .querySelectorAll('[data-toggle="popover"]')
    .forEach((popover) => {
      popover.removeAttribute("data-content");
      popover.removeAttribute("data-original-title");
    });
};

// Initialize all array inputs on page load
document.addEventListener("DOMContentLoaded", function () {
  // Debug info - log all available UUIDs
  console.log(
    "Available reset buttons:",
    Array.from(document.querySelectorAll(".reset-button[data-table-uuid]")).map(
      (el) => el.getAttribute("data-table-uuid")
    )
  );

  // Try different selector strategies
  const resetButtons = document.querySelectorAll(
    ".reset-button[data-table-uuid]"
  );

  if (resetButtons.length === 0) {
    console.error("No reset buttons found on the page");
  }

  resetButtons.forEach((button) => {
    try {
      const uuid = button.getAttribute("data-table-uuid");
      console.log("Initializing PLArrayInput for UUID:", uuid);
      new window.PLArrayInput(uuid);
    } catch (e) {
      console.error("Error initializing array input:", e);
    }
  });
});
