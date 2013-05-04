import os
from optparse import OptionParser

def report_bug(data):
    from enfold.http.client import opener

    if not 'credentials' in data:
        data['credentials'] = 'feedback:10.39:8080/P'

    feedback_url = 'http://feedback.enfoldsystems.com/report_bug'
    return opener.open(feedback_url, data).read()

if __name__ == '__main__':
    opts = ['desktop_available_seats',
            'desktop_allocated_seats',
            'subject',
            'message']

    for product in ('desktop', 'server', 'proxy'):
        for info in ('email', 'days_left', 'version', 'log'):
            opts.append('%s_%s' % (product, info))

    parser = OptionParser()
    parser.add_option('', '--credentials')
    for opt in opts:
        parser.add_option('', '--' + opt.replace('_', '-'))

    options, args = parser.parse_args()

    data = {}
    for key, value in options.__dict__.items():
        if value is None:
            continue
        if key.endswith('_log'):
            fname = os.path.expanduser(value)
            if not os.path.exists(fname) or not os.path.isfile(fname):
                parser.error('Not a valid file: %r' % fname)
            else:
                value = open(fname, mode='rb')
        data[key] = value
    print report_bug(data)
