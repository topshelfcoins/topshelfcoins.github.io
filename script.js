function setFilters() {
  const allFilterBtns = document.querySelectorAll('.filter-btn');
  allFilterBtns.forEach((btn) => {
    btn.addEventListener('click', () => {
      showFilteredContent(btn);
    });
  });
}

function showFilteredContent(btn){
  const allFilterItems = document.querySelectorAll('.product');
  allFilterItems.forEach((item) => {
    if(item.classList.contains(btn.id)){
      item.style.display = "block";
    } else {
        item.style.display = "none";
    }
  });
}