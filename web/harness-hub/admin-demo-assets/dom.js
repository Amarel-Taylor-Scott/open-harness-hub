export function $(selector, root) {
  return (root || document).querySelector(selector);
}

export function esc(value) {
  return String(value == null ? "" : value).replace(/[&<>"]/g, function (char) {
    return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[char];
  });
}

export function setText(selector, value) {
  var node = $(selector);
  if (node) node.textContent = value;
}
