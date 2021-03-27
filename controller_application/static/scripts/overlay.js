var pollingSpeed = 500; //in ms
var winner_switch = new Boolean(false);

function updateInformation() {
	$.ajax({
		type: "GET",
		contentType: "application/json",
		url: "http://127.0.0.1:5000/out.json",
		success: function(json) {
            $("#player_container").empty()
            //Populate player list
            for(var i = 0; i < json.player_count; i++) {
                if(json.players.hasOwnProperty((i+1))) {
                    $("#player_container").append(`<div id='player` + (i+1) + `_container' class='player'>
                                                    <a id='player` + (i+1) + `_name' class='name'>` + json.players[(i+1)]["name"] + `</a>
                                                    <a id='player` + (i+1) + `_score' class='score'>` + json.players[(i+1)]["wins"] + `</a>
                                                </div>`)
                }
            }
            //Display winner
            if(json.hasOwnProperty("winner")) {
                //only display if hasnt already been displayed
                if(winner_switch) {
                    winner_switch = false
                    id = json["winner"]
                    $("#winner_container").show()
                    $("#winner_container").append(json.players[id]["name"] + " wins!")
                    setTimeout(function(){ $('#winner_container').fadeOut() }, 3000);
                }
            } else {
                $("#winner_container").empty()
                winner_switch = true
            }
        }
	})
    //Loop ever 0.5 seconds
	setTimeout("updateInformation()", pollingSpeed);
}
 
$(document).ready(function() {
	updateInformation();
});