const dificulty = 1;
const timeout = 5;

window.onload = function (event) {
    const form = document.getElementById('emailForm');
    const btnSubmit = document.querySelector('button[form="' + form.id + '"]');

    const mine = function(event) {
        event.preventDefault();

        if (typeof CryptoJS == 'undefined') {
            console.log('CryptoJS not loaded')
            return;
        }

        const lastProof = form.querySelector('#last_proof').value;
        const lastHash = form.querySelector('#last_hash').value;
        const proofInput = form.querySelector('#proof');

        const register = function (proof) {
            console.log('proof found: ' + proof);
            proofInput.value = proof;
            form.submit();
        }

        const memoryProof = window.localStorage.getItem(lastHash); 
        if (memoryProof) {
            window.localStorage.removeItem(lastHash);            
            return register(memoryProof);
        }

        btnSubmit.setAttribute('disabled', '')

        let proof = 0;
        const timer = setInterval(function () {
            if (isValidProof('' + lastProof + proof + lastHash)) {
                clearInterval(timer);
                btnSubmit.removeAttribute('disabled');
                window.localStorage.setItem(lastHash, proof);
                register(proof);
            } else {
                proof++;
            }
        }, 100)

        // stop function
        setTimeout(function () {
            clearInterval(timer);
            console.log('POW took too long. Try again.')
            btnSubmit.removeAttribute('disabled');
        }, 60000 * timeout);
    }
    
    form.addEventListener('submit', mine);
}

function isValidProof(pOfWork) {
    if (pOfWork.length < dificulty) {
        throw new Exception('Invalid proof length');
    }

    let hashText = String(CryptoJS.SHA256(pOfWork)); 
    console.log('hash: ' + hashText)

    const table = document.getElementById('hashTable');
    table.textContent = table.textContent + "\n" + hashText;
    table.scrollTop = table.scrollHeight;

    let lastWords = '';
    let zeroes = ''
    for (let index = 1; index <= dificulty; index++) {
        lastWords = hashText.charAt(hashText.length - index) + lastWords;
        zeroes += '0'
    }

    console.log('lastWords: ' + lastWords)
    return lastWords === zeroes;
}
