document.addEventListener('DOMContentLoaded', function() {
    const startBtn = document.getElementById('startBtn');
    const pauseBtn = document.getElementById('pauseBtn');


    const volVal = document.getElementById('vol-val');
    const distVal = document.getElementById('dist-val');
    const accVal = document.getElementById('acc-val');
    const timeVal = document.getElementById('time-val');

    const cardOpen = document.getElementById('card-open');
    const cardPinch = document.getElementById('card-pinch');
    const cardClosed = document.getElementById('card-closed');

    function sendCommand(command) {
        fetch(`/${command}`, { method: 'POST' })
            .then(response => response.json())
            .then(data => console.log(data.status));
    }

    startBtn.addEventListener('click', () => sendCommand('start'));
    pauseBtn.addEventListener('click', () => sendCommand('pause'));

    function updateUI(data) {

        volVal.innerText = data.current_volume + '%';
        distVal.innerText = data.finger_distance_mm + 'mm';
        accVal.innerText = data.accuracy + '%';
        timeVal.innerText = data.response_time_ms + 'ms';


        [cardOpen, cardPinch, cardClosed].forEach(card => {
            card.classList.remove('active-card');
            card.querySelector('.status').innerText = 'Inactive';
            card.querySelector('.status').classList.remove('active');
            card.querySelector('.status').classList.add('inactive');
        });


        let activeCard = null;
        if (data.current_gesture === 'Open Hand') activeCard = cardOpen;
        else if (data.current_gesture === 'Pinch') activeCard = cardPinch;
        else if (data.current_gesture === 'Closed') activeCard = cardClosed;

        if (activeCard) {
            activeCard.classList.add('active-card');
            const statusEl = activeCard.querySelector('.status');
            statusEl.innerText = 'Active';
            statusEl.classList.remove('inactive');
            statusEl.classList.add('active');
        }
    }


    setInterval(() => {
        fetch('/get_data')
            .then(response => response.json())
            .then(data => {
                if (data.is_running) {
                    updateUI(data);
                }
            });
    }, 100);


    sendCommand('pause');
});