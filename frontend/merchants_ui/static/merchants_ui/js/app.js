(function () {
  "use strict";

  function formatCNPJ(raw) {
    // CNPJ alfanumérico: os 12 primeiros caracteres podem ser dígitos ou
    // letras (maiúsculas), os 2 dígitos verificadores finais são sempre numéricos.
    var chars = (raw || "").replace(/[^0-9A-Za-z]/g, "").toUpperCase().slice(0, 14);
    var head = chars.slice(0, 12);
    var tail = chars.slice(12).replace(/\D/g, "");
    chars = head + tail;
    if (chars.length > 12) {
      return chars.replace(/(.{2})(.{3})(.{3})(.{4})(.{0,2})/, "$1.$2.$3/$4-$5");
    }
    if (chars.length > 8) {
      return chars.replace(/(.{2})(.{3})(.{3})(.{0,4})/, "$1.$2.$3/$4");
    }
    if (chars.length > 5) {
      return chars.replace(/(.{2})(.{3})(.{0,3})/, "$1.$2.$3");
    }
    if (chars.length > 2) {
      return chars.replace(/(.{2})(.{0,3})/, "$1.$2");
    }
    return chars;
  }

  function formatPhone(raw) {
    var digits = (raw || "").replace(/\D/g, "").slice(0, 11);
    if (digits.length > 10) {
      return digits.replace(/(\d{2})(\d{5})(\d{0,4})/, "($1) $2-$3");
    }
    if (digits.length > 6) {
      return digits.replace(/(\d{2})(\d{4})(\d{0,4})/, "($1) $2-$3");
    }
    if (digits.length > 2) {
      return digits.replace(/(\d{2})(\d{0,4})/, "($1) $2");
    }
    if (digits.length > 0) {
      return "(" + digits;
    }
    return digits;
  }

  function attachMask(input, formatter) {
    if (!input) return;
    var apply = function () {
      input.value = formatter(input.value);
    };
    apply();
    input.addEventListener("input", apply);
  }

  function setupMasks() {
    attachMask(document.getElementById("id_cnpj"), formatCNPJ);
    attachMask(document.getElementById("id_telefone"), formatPhone);
  }

  function setupMessageAutoDismiss() {
    var items = document.querySelectorAll(".messages li");
    items.forEach(function (item) {
      setTimeout(function () {
        item.classList.add("fade-out");
        item.addEventListener("transitionend", function () {
          item.remove();
        });
      }, 4000);
    });
  }

  document.addEventListener("DOMContentLoaded", function () {
    setupMasks();
    setupMessageAutoDismiss();
  });
})();
