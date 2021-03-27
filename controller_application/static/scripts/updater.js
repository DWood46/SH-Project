var obs;

function update_scene() {
    if(obs !== null) {
        scene = $("#scenes :selected").text();
        obs.send('SetCurrentScene', {'scene-name': scene});
    }
}

function update_game() {
    game = $("#games :selected").val();
    $.post(
        "update_game",
        {"game": game},
        function(data, status){
            setTimeout(() => {
                location.reload();
            }, 1500);
            
        }
    );
}

function update_names() {
    object = {}
    $(".name_input").each(function(index) {
        object[index+1] = $(this).val();
    })
    $.post(
        "update",
        object,
        function(data, status){
           console.log("Submitted names");
        }
    );
}

function populate_inputs(data) {
    const count = data.player_count
    //Create inputs for each player
    for(var i = 1; i <= count; i++) {
        if(i > 16) {
            break;
        }
        $("#names_box").append("<label for='player" + i + "_name'>Player " + i + " Name</label><br>")
        $("#names_box").append("<input type='text' class='name_input' id='player" + i + "_name'></input><br><br>")
        //Populate if values already available
        if(data.players.hasOwnProperty(i)) {
            $("#player" + i + "_name").val(data.players[i]["name"])
        }
    }
    //Add submit button if necessary
    if(count > 0) {
        $("#names_box").append("<br><button id='update_names' class='name' onclick='update_names()'>Update names</button>")
    }
    //Populate games list
    for(var a = 0; a < data.games.length; a++) {
        $("#games").append(new Option(data.games[a], a));
    }

}

$(document).ready(function(){
    obs = new OBSWebSocket();
    obs.connect({
            address: obs_host, password: obs_pass
        })
        .then(() => {
            $("#scenes").show();
            $("#update_scene").show();
            obs.send(
                'GetSceneList', {}
            )
            .then(function(value) {
                value["scenes"].forEach(function(scene) {
                    $("#scenes").append(new Option(scene["name"], scene["name"]));
                })
                $("#scenes").val(value["current-scene"])
                //console.log(value);
            })
        })
        .catch(err => {
            console.log("OBS connection failed - hiding scene changer");
            obs = null;
            $("#scene_box").hide();
        });

	$.getJSON("/out.json", function(data) {
        populate_inputs(data)
	});
});