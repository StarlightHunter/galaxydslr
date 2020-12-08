// AstroCamWeb
// Author: Oliver Gutierrez <ogutsua@gmail.com>

"use_strict";

var GIF_BASE64_PIXEL =
  "data:image/gif;base64,R0lGODlhAQABAIAAAP///wAAACH5BAEAAAAALAAAAAABAAEAAAICRAEAOw==";

var CAMERA_SETTINGS = ["aperture", "iso"];

var FORCED_CAMERA_SETTINGS = {
  shutterspeed: "bulb",
  drivemode: "Single",
  aeb: "off",
  whitebalance: "Daylight",
  colorspace: "sRGB",
  picturestyle: "Faithful",
  imageformat: "RAW + Large Fine JPEG",
  capturetarget: "Memory card",
};

var capture_status_interval = null;
var last_capture = 0;

// Send data to server
function get_data(url, success_cb, error_cb) {
  $.ajax({
    type: "GET",
    url: url,
    dataType: "json",
    success: function (response) {
      if (typeof success_cb == "function") {
        success_cb(response);
      }
    },
    error: function (err) {
      if (typeof error_cb == "function") {
        error_cb(err);
      } else {
        console.log(err);
      }
    },
  });
}

// Send data to server
function send_data(url, data, success_cb, error_cb) {
  $.ajax({
    type: "POST",
    url: url,
    data: data,
    dataType: "json",
    success: function (response) {
      if (typeof success_cb == "function") {
        success_cb(response);
      }
    },
    error: function (err) {
      if (typeof error_cb == "function") {
        error_cb(err);
      } else {
        console.log(err);
      }
    },
  });
}

// Populate configuration choices
function populate_configuration_choices(option, choices, current, empty, disable) {
  disable = disable || true;
  empty = empty || false;
  var elem = $("#" + option);
  if (elem) {
    if (disable) {
      elem.prop("disabled", true);
    }
    elem.html("");
    if (empty) {
      opt = $("<option />").val("").text("---");
      if (current === null) opt.attr("selected", true);
      elem.append(opt);
    }
    var opt,
      text,
      value = null;
    $.each(choices, function () {
      if (Array.isArray(this)) {
        text = this[0];
        value = this[1];
      } else {
        text = this;
        value = this;
      }
      opt = $("<option />").val(value).text(text);
      if (value == current) opt.attr("selected", true);
      elem.append(opt);
    });
    if (disable) {
      elem.prop("disabled", false);
    }
  }
}

function set_status_value(
  elementid,
  status,
  enabled_text,
  disabled_text,
  enabled_class,
  disabled_class
) {
  enabled_class = enabled_class || "status_enabled";
  disabled_class = disabled_class || "status_disabled";
  elem = $("#" + elementid);
  if (status) {
    elem.removeClass(disabled_class).addClass(enabled_class);
    status_text = enabled_text;
  } else {
    elem.removeClass(enabled_class).addClass(disabled_class);
    status_text = disabled_text;
  }
  elem.val(status_text);
}

function setup_gui(mode) {
  // Camera connected
  if (mode == "camera_connected") {
    // Change text of camera connect button to Disconnect
    $("#camera_connection_button").text("Disconnect");
    // Change camera status to connected
    set_status_value("camera_connection_status", true, "Connected", "Disconnected");
    // Disable camera selection
    $("#camera_list").prop("disabled", true);
    // Show camera settings
    $("#camera_settings").collapse("show");
    // Show capture controls
    $("#capture_controls").collapse("show");
    // Disable reload cameras button
    $("#reload_cameras_button").prop("disabled", true);
  }

  // Camera disconnected
  if (mode == "camera_disconnected") {
    // Change text of camera connect button to Connect
    $("#camera_connection_button").text("Connect");
    // Change camera status to disconnected
    set_status_value("camera_connection_status", false, "Connected", "Disconnected");
    // Enable camera selection
    $("#camera_list").prop("disabled", false);
    // Hide camera settings
    $("#camera_settings").collapse("hide");
    // Hide capture controls
    $("#capture_controls").collapse("hide");
    // Enable reload cameras buton
    $("#reload_cameras_button").prop("disabled", false);
  }

  // Capturing preview
  if (mode == "camera_capturing_preview") {
    // Disable preview capture button
    $("#camera_preview_button").prop("disabled", true);
    $("#capture_toggle_button").prop("disabled", true);
  }

  // Finished capturing preview
  if (mode == "camera_finished_capturing_preview") {
    // Enable preview capture button
    $("#camera_preview_button").prop("disabled", false);
    $("#capture_toggle_button").prop("disabled", false);
  }

  // Start capturing
  if (mode == "started_capturing") {
    $("#capture_toggle_button > span.oi")
      .removeClass("oi-media-play")
      .addClass("oi-media-stop");
  }

  // Stop capturing
  if (mode == "stopped_capturing") {
    $("#capture_toggle_button > span.oi")
      .removeClass("oi-media-stop")
      .addClass("oi-media-play");
  }

  // Capturing preview or sequence
  if (mode == "started_capturing" || mode == "camera_capturing_preview") {
    // Disable preview capture button
    $("#camera_preview_button").prop("disabled", true);
    $("#camera_connection_button").prop("disabled", true);
    $("#exposure").prop("disabled", true);
    $("#aperture").prop("disabled", true);
    $("#iso").prop("disabled", true);
    $("#captures").prop("disabled", true);
    $("#guider_connection_button").prop("disabled", true);
    $("#dither").prop("disabled", true);
    $("#dither_n").prop("disabled", true);
    $("#dither_px").prop("disabled", true);
    $("#settle_px").prop("disabled", true);
    $("#settle_time").prop("disabled", true);
    $("#settle_timeout").prop("disabled", true);
  }

  // Finished capturing preview
  if (mode == "stopped_capturing" || mode == "camera_finished_capturing_preview") {
    // Enable preview capture button
    $("#camera_preview_button").prop("disabled", false);
    $("#camera_connection_button").prop("disabled", false);
    $("#exposure").prop("disabled", false);
    $("#aperture").prop("disabled", false);
    $("#iso").prop("disabled", false);
    $("#captures").prop("disabled", false);
    $("#guider_connection_button").prop("disabled", true);
    $("#dither").prop("disabled", false);
    $("#dither_n").prop("disabled", false);
    $("#dither_px").prop("disabled", false);
    $("#settle_px").prop("disabled", false);
    $("#settle_time").prop("disabled", false);
    $("#settle_timeout").prop("disabled", false);
  }

  // Guider connected
  if (mode == "guider_connected") {
    // Change text of guider connect button to Disconnect
    $("#guider_connection_button").text("Disconnect");
    // Show guider settings
    $("#guider_settings").collapse("show");
    // Change guider status to connected
    set_status_value("guider_connection_status", true, "Connected", "Disconnected");
  }

  // Guider disconnected
  if (mode == "guider_disconnected") {
    // Change text of guider connect button to Connect
    $("#guider_connection_button").text("Connect");
    // Hide guider settings
    $("#guider_settings").collapse("hide");
    // Change guider status to disconnected
    set_status_value("guider_connection_status", false, "Connected", "Disconnected");
  }
}

function show_image(image_data) {
  $("#current_image").attr("src", "data:image/jpg;base64," + image_data);
}

function connect_camera() {
  // Connect camera
  var port = $("#camera_list").val();
  if (port) {
    log_message("Connecting camera at port " + port);
    send_data("/camera/connect/", { port: port }, function (response) {
      if (response.status) {
        console.log("Camera connected");
        // Load camera configuration and set forced values
        load_camera_config(set_camera_config);
        setup_gui("camera_connected");
      } else {
        console.log("Error connecting camera: ", response.error);
      }
    });
  } else {
    log_message("No camera has been selected");
  }
}

function disconnect_camera() {
  // Disconnect camera
  send_data("/camera/disconnect/", {}, function (response) {
    if (response.status) {
      log_message("Camera disconnected");
      setup_gui("camera_disconnected");
    } else {
      log_message("Error disconnecting camera: " + response.error);
    }
  });
}

// Load camera configuration
function load_camera_config(cb) {
  log_message("Loading camera settings");
  get_data("/camera/config/", function (response) {
    if (response.status) {
      console.log("Configuration read:", response);
      config = response.config;
      $.each(CAMERA_SETTINGS, function (index, name) {
        console.log(name, config[name]);
        populate_configuration_choices(
          name,
          config[name].choices,
          config[name].current
        );
      });
      if (typeof cb == "function") {
        console.log("Executing callback from load_camera_config");
        cb(response);
      }
    } else {
      log_message("Error reading camera configuration");
    }
  });
}

// Set camera configuration
function set_camera_config(cb) {
  log_message("Updating camera settings");
  var data = {};
  // Collect settings
  $.each(CAMERA_SETTINGS, function () {
    data[this] = $("#" + this).val();
  });
  // Forced settings
  $.each(FORCED_CAMERA_SETTINGS, function (elem, value) {
    data[elem] = value;
  });
  console.log("Config to be set:", data);
  send_data("/camera/config/", data, function (response) {
    if (response.status) {
      console.log("Camera configuration set.", response);
      log_message("Camera settings updated");
    } else {
      log_message("Error setting camera configuration.", response);
    }
    if (typeof cb == "function") {
      console.log("Executing callback from set_camera_config");
      cb(response);
    }
  });
}

// Get camera preview
function get_camera_preview(cb) {
  log_message("Getting camera preview");
  // First apply camera config to ensure configuration is set
  set_camera_config(function () {
    var exposure = $("#exposure").val();
    var data = { exposure: exposure };
    setup_gui("camera_capturing_preview");
    send_data("/camera/preview/", data, function (response) {
      if (response.status) {
        console.log("Got camera preview");
        log_message("Retrieved camera preview");
        show_image(response.image_data);
      } else {
        console.log("Error getting camera preview", response);
        log_message("Error getting camera preview");
      }
      setup_gui("camera_finished_capturing_preview");
      if (typeof cb == "function") {
        console.log("Executing callback from get_camera_preview");
        cb(response);
      }
    });
  });
}

// Start capturing
function start_capturing(cb) {
  log_message("Starting capture process");
  // First apply camera config to ensure configuration is set
  set_camera_config(function () {
    var data = {
      exposure: $("#exposure").val(),
      captures: $("#captures").val(),
      dither: $("#dither").prop("checked"),
      dither_n: $("#dither_n").val(),
      dither_px: $("#dither_px").val(),
      settle_px: $("#settle_px").val(),
      settle_time: $("#settle_time").val(),
      settle_timeout: $("#settle_timeout").val(),
    };
    console.log("Capture settings", data);
    $("#capture_status").val("0 / " + data.captures);
    last_capture = 0;
    send_data("/capture/start/", data, function (response) {
      if (response.status) {
        setup_gui("started_capturing");
        log_message("Capture process started");
        // Setup status checking function
        capture_status_interval = setInterval(get_capture_status, 1000);
      } else {
        console.log("Error starting capture process", response);
      }
      if (typeof cb == "function") {
        console.log("Executing callback from start_capturing");
        cb(response);
      }
    });
  });
}

// Stop capturing
function stop_capturing(cb) {
  log_message("Stopping capturing");
  // First apply camera config to ensure configuration is set
  send_data("/capture/stop/", {}, function (response) {
    if (response.status) {
      setup_gui("stopped_capturing");
      log_message("Capture process stopped");
      // Stop status checking function
      clearInterval(capture_status_interval);
    } else {
      console.log("Error stopping capture process", response);
      log_message("Error stopping capture process");
    }
    if (typeof cb == "function") {
      console.log("Executing callback from stop_capturing");
      cb(response);
    }
  });
}

// Get capture status
function get_capture_status(cb) {
  var capture_status = {
    IDLE: 0,
    CAPTURING: 1,
    DITHERING: 2,
    STOPPING: 3,
  };

  get_data("/capture/status/", function (response) {
    if (response.status) {
      console.log("Capture status retrieved", response);
      var status = response.capture_status;
      if (
        status.current_status === capture_status.CAPTURING ||
        status.current_status === capture_status.DITHERING
      ) {
        console.log("Capture process ongoing");
        // Update capture number if needed
        update_capture_status(status);
      } else {
        // Update capture status for the last time
        update_capture_status(status);
        // Setup GUI to stopped capturing status
        setup_gui("stopped_capturing");
        clearInterval(capture_status_interval);
        log_message("Capture process has finished");
      }
    } else {
      console.log("Error getting capture status", response);
    }
    if (typeof cb == "function") {
      console.log("Executing callback from stop_capturing");
      cb(response);
    }
  });
}

// Update capture status
function update_capture_status(capture_status) {
  var status =
    capture_status.current_capture + " / " + capture_status.capture_parms.captures;
  if ($("#capture_status").val() !== status) {
    $("#capture_status").val(status);
  }
  if (last_capture !== capture_status.last_capture) {
    // Load last image and display it
    last_capture = capture_status.last_capture;
    var image_status =
      capture_status.last_capture + " / " + capture_status.capture_parms.captures;
    log_message("Loading image " + status);
    get_data("/capture/last_image/", function (response) {
      if (response.status) {
        console.log("Got image data");
        if (response.image_data !== null) {
          show_image(response.image_data);
          log_message("Loaded image " + image_status + " successfully");
        }
      } else {
        console.log("Error getting image data", response);
        log_message("Error loading image" + current_image_status);
      }
    });
  }
  if (capture_status.dither_status) {
    console.log("Dithering status:", capture_status.dither_status);
    var ds = capture_status.dither_status;
    log_message(
      "Dithering: Dist: " +
        ds.dist +
        ", Pixels: " +
        ds.px +
        ", Time: " +
        ds.time +
        ", Settle time: " +
        ds.settle_time
    );
  }
}

function log_message(message) {
  var current_content = $("#logarea").html();
  var date = new Date().toJSON();
  $("#logarea").html(current_content + "<div>[" + date + "]: " + message + "</div>");
  $("#logarea").scrollTop($("#logarea").prop("scrollHeight"));
}

function get_camera_list() {
  log_message("Getting camera list");
  get_data("/camera/list/", function (response) {
    if (response.status) {
      log_message("Camera list retrieved");
      populate_configuration_choices(
        "camera_list",
        response.camera_list.choices,
        response.camera_list.current,
        true
      );
    } else {
      log_message("Error getting camera list");
      log_message("Error getting camera list: " + response.error);
    }
  });
}

function initialize_app() {
  get_data("/status/", function (response) {
    console.log("Read status: ", response);
    if (response.status) {
      if (response.locked) {
        // Retry
        log_message("Application is busy. Retrying.");
        setTimeout(initialize_app, 1000);
      } else {
        // Populate camera list
        populate_configuration_choices(
          "camera_list",
          response.camera_list.choices,
          response.camera_list.current,
          true
        );
        if (response.camera_config) {
          // Load camera configuration
          console.log("Current camera config:", response.camera_config);
          $.each(response.camera_config, function (elem) {
            populate_configuration_choices(
              elem,
              response.camera_config[elem].choices,
              response.camera_config[elem].current
            );
          });
          // Camera is connected. Set status accordingly
          log_message("Camera already connected");
          setup_gui("camera_connected");
        }
        if (response.guider_connected) {
          // Guider is connected. Set status accordingly
          log_message("Guider already connected");
          setup_gui("guider_connected");
        }
        if (response.capturing) {
          log_message("Retaking ongoing capture process");
          setup_gui("started_capturing");
          // Setup status checking function
          capture_status_interval = setInterval(get_capture_status, 1000);
        }
      }
    } else {
      log_message("Error getting initial status. Retrying.");
      console.log("Error getting initial status", response);
      setTimeout(initialize_app, 1000);
    }
    // Hide initial loading screen
    $("#initial_loading").addClass("fade_out");
    setTimeout(function () {
      $("#initial_loading").hide();
      log_message("Initialization done");
    }, 1000);
  });
}

function connect_guider() {
  // Connect guider
  var host = "localhost";
  log_message("Connecting with autoguider on " + host);
  send_data("/guider/connect/", { host: host }, function (response) {
    if (response.status) {
      console.log("Guider connected");
      // Load camera configuration and set forced values
      load_camera_config(set_camera_config);
      setup_gui("guider_connected");
    } else {
      console.log("Error connecting guider: ", response.error);
    }
  });
}

function disconnect_guider() {
  // Disconnect guider
  send_data("/guider/disconnect/", {}, function (response) {
    if (response.status) {
      log_message("Guider disconnected");
      setup_gui("guider_disconnected");
    } else {
      log_message("Error disconnecting guider: " + response.error);
    }
  });
}

$(document).ready(function () {
  // Event binding
  $("#sidebar_toggler").on("click", function () {
    $("#sidebar").toggleClass("active");
    if ($("#sidebar").hasClass("active")) {
      $("#sidebar_toggler span.oi")
        .removeClass("oi-arrow-left")
        .addClass("oi-arrow-right");
    } else {
      $("#sidebar_toggler span.oi")
        .removeClass("oi-arrow-right")
        .addClass("oi-arrow-left");
    }
  });

  // Reload camera list button
  $("#reload_cameras_button").on("click", function () {
    get_camera_list();
  });

  // Toggle camera connection button
  $("#camera_connection_button").on("click", function () {
    if ($("#camera_connection_button").text().trim() === "Connect") {
      connect_camera();
    } else {
      disconnect_camera();
    }
  });

  // Toggle guider connection button
  $("#guider_connection_button").on("click", function () {
    if ($("#guider_connection_button").text().trim() === "Connect") {
      connect_guider();
    } else {
      disconnect_guider();
    }
  });

  // Camera preview button
  $("#camera_preview_button").on("click", function () {
    get_camera_preview();
  });

  // Apply camera settings when changed
  $("#aperture, #iso").change(function () {
    set_camera_config();
  });

  // Toggle capturing button
  $("#capture_toggle_button").on("click", function () {
    if ($("#capture_toggle_button > span.oi").hasClass("oi-media-play")) {
      start_capturing();
    } else {
      stop_capturing();
    }
  });

  // Load initial data and setup interface
  log_message("Initlializing");
  initialize_app();
});
