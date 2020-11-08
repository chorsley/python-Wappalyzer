function togglePrivate() {
    // Hide all private things by adding the private-hidden class to them.
    document.body.classList.toggle("private-hidden");

    var button = document.querySelector('#showPrivate button');
    if(document.body.classList.contains('private-hidden')) {
        button.innerText = 'Show Private API';
    } else {
        button.innerText = 'Hide Private API';
    }
}
// On load, hide everything private
togglePrivate()
