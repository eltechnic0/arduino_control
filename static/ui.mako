<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
  <title>Arduino Control</title>

  <meta charset="utf-8" />
  <meta http-equiv="Content-type" content="text/html; charset=utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <script src="https://code.jquery.com/jquery-2.1.3.min.js"></script>
  <script type="text/javascript" src="/static/jquery.noty.packaged.min.js"></script>
  <script src="/static/ui.js"></script>
  <style>
  body {
    margin:0;
    padding:0;
  }
  .left-column {
    float:left;
    padding:10px;
    padding-top:0px;
  }
  .right-column {
    float:left;
    padding:10px;
    padding-top:0px;
  }
  .center-column {
    float:left;
    padding:10px;
    padding-top:0px;
  }
  .grid-opts{
    margin:5px;
  }
  .tight-list{
    list-style-type:none;
    padding:0px;
    margin:0px;
    max-width:500px;
  }
  /*#script-history-list li:hover,
  #comm-msg-hist-list li:hover {
    background-color:#f1f1f1;
    cursor:pointer;
  }*/
  .clickable :hover {
    background-color:#f1f1f1;
    cursor:pointer;
  }
  .clickable {
    text-decoration: underline;
    color:blue
  }
  .modal {
    position:fixed;
    left:50px;
    top:50px;
    padding:10px;
    border: 1px solid black;
    border-radius: 4px;
    box-shadow: 0px 0px 4px black;
    background-color: white;
  }
  </style>
</head>
<body>
  <div id="modal-container"></div>
  <div class="left-column">
    <div class="connection">
      <h1>Connection</h1>
      <button id="connect-button" name="connect">Connect</button>
      <button id="reconnect-button" name="reconnect">Reconnect</button>
      <button id="disconnect-button" name="disconnect">Disconnect</button>
      <h3 id="conn-state-text">Disconnected</h3>
      <!-- <label><input type="checkbox" id="verbose-checkbox" value="">Verbose mode</label>
      <button id="comtest-button" name="comtest">Comtest</button> -->
    </div>
    <div class='vset'>
      <h1>VSet</h1>
      <div>
        <input type="text" name="batch" placeholder="p1 ... p4, v1 ... v4"/>
        <button id="vset-button" name="send">Send</button>
        <table>
          <tr>
            <th>Pin</th>
            <th>Value</th>
          </tr>
          <tr>
            <td>3</td>
            <td><input type="text" name="value" size="4" placeholder="0..1"/></td>
            <td><button name="0">Send</button></td>
          </tr>
          <tr>
            <td>9</td>
            <td><input type="text" name="value" size="4" placeholder="0..1"/></td>
            <td><button name="1">Send</button></td>
          </tr>
          <tr>
            <td>10</td>
            <td><input type="text" name="value" size="4" placeholder="0..1"/></td>
            <td><button name="2">Send</button></td>
          <tr>
          </tr>
            <td>11</td>
            <td><input type="text" name="value" size="4" placeholder="0..1"/></td>
            <td><button name="3">Send</button></td>
          </tr>
        </table>
      </div>
    </div>
    <div class='vread'>
      <h1>VRead</h1>
      <div>
        <input type="text" name="batch" placeholder="p1 ... p4"/>
        <button id="vread-button" name="send">Read</button>
        <table>
          <tr>
            <th>Pin</th>
            <th>Value</th>
          </tr>
          <tr>
            <td>0</td>
            <td class="vread-value">0.0</td>
            <td><button name="0">Read</button></td>
          </tr>
          <tr>
            <td>1</td>
            <td class="vread-value">0.0</td>
            <td><button name="1">Read</button></td>
          </tr>
          <tr>
            <td>2</td>
            <td class="vread-value">0.0</td>
            <td><button name="2">Read</button></td>
          </tr>
          <tr>
            <td>3</td>
            <td class="vread-value">0.0</td>
            <td><button name="3">Read</button></td>
          </tr>
        </table>
      </div>
    </div>
  </div>
  <div class="center-column">
    <div>
      <h1>VSet Grid</h1>
      <img id="cuadricula" src="static/cuadricula.png" alt="grid" style="width:100%;max-width:450px"><br>
      <div class="grid-opts">
        <table>
          <tr>
            <th>X</th>
            <th>Y</th>
          </tr>
          <tr>
            <td><input type="text" name="x" size="4" value="0"/></td>
            <td><input type="text" name="y" size="4" value="0"/></td>
            <td><button name="send">Send</button><td>
            <td><button name="reset">Reset</button></td>
            <td><label><input type="checkbox" id="autosend-checkbox" value="0" checked>Autosend</label></td>
          </tr>
        </table>
        <table>
          <tr>
            <th>Settling</th>
            <th>Resolution</th>
          </tr>
          <tr>
            <td><input type="text" name="settling" size="4" value="250"></td>
            <td><input type="text" name="resolution" size="4" value="5"></td>
          </tr>
        </table>
        <table>
          <tr>
            <th>Right</th>
            <th>Top</th>
            <th>Left</th>
            <th>Bottom</th>
          </tr>
          <tr>
            <td><input type="text" name="right" size="4" value="3"></td>
            <td><input type="text" name="top" size="4" value="9"></td>
            <td><input type="text" name="left" size="4" value="10"></td>
            <td><input type="text" name="bottom" size="4" value="11"></td>
          </tr>
        </table>
      </div>
    </div>
  </div>
  <div class="right-column">
    <div class="scripts">
      <h1>Plugins</h1>
      <table>
        <td>
          <textarea id="script-textbox" cols="35" rows="5"></textarea>
        </td>
        <td style="vertical-align:top">
          <button>Send</button>
        </td>
      </table>
      <h4 style="margin-bottom:0px">Script history</h4>
      <ul class="clickable tight-list" id="script-history-list">
        <li>{"fname":"script_test","string":"Hello world!","array":[1,2,3]}</li>
      </ul>
    </div>
    <div>
      <h4 style="margin-bottom:0px">Interactive</h4>
      <ul id="addon-list" class="clickable tight-list" style="text-decoration:underline">
        <!-- <li name="/calibration/index">Camera calibration</li> -->
        <!-- template - mako for-loop over the addons -->
      % for addon in addons:
        <li name="${addon['url']}">${addon['text']}</li>
      % endfor
      </ul>
    </div>
    <div>
      <h1>Communications</h1>
      <ul class="clickable tight-list" id="comm-msg-hist-list">
      </ul>
    </div>
  </div>
</body>
</html>
