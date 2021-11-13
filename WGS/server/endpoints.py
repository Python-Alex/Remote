import sys
import flask
import actions

sys.stdout.write(f'[*] Loading Reference {__name__}\n')

flask_client : flask.Flask = flask.Flask(__name__)

def ensure_integrity(headers, pdata: dict) -> bool:
    header_insurance = False

    if(not headers.get('User-Agent') or headers.get('User-Agent') != 'python-requests'):
        header_insurance = True

    if(not pdata['content']):    
        header_insurance = False

    return header_insurance

@flask_client.route('/register_action', methods=['POST'])
def register_packet_action() -> None:
    packet_data = flask.request.get_json()
    packet_headers = flask.request.headers

    if(not ensure_integrity(packet_headers, packet_data)):
        return {
            'error': 0xE1,
            'message': 'bad integrity'
        }, 400

    rcallback = actions.reverse_aflag_map[int(packet_data.get('flag'))]
    rcallback(flask.request, **packet_data)

    return ""

flask_client.run('127.0.0.1', 9999)