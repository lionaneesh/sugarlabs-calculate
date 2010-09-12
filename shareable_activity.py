import dbus
from dbus import Interface
from dbus.service import method, signal
import telepathy

from sugar.activity import activity
from sugar.presence import presenceservice
from sugar.presence.sugartubeconn import SugarTubeConnection

import logging
_logger = logging.getLogger('ShareableActivity')

IFACE = 'org.laptop.ShareableActivity'

class ShareableObject(dbus.service.Object):

    def __init__(self, tube, path):
        dbus.service.Object.__init__(self, tube, path)

    @dbus.service.signal(dbus_interface=IFACE, signature='sv')
    def SendMessage(self, msg, kwargs):
        pass

    @dbus.service.signal(dbus_interface=IFACE, signature='ssv')
    def SendMessageTo(self, busname, msg, kwargs):
        pass

class ShareableActivity(activity.Activity):
    '''
    A shareable activity.

    Signals to connect to for more notifications:
        self.get_shared_activity().connect('buddy-joined', ...)
        self.get_shared_activity().connect('buddy-left', ...)
    '''

    def __init__(self, handle, *args, **kwargs):
        '''
        Initialize the ShareableActivity class.

        Kwargs:
            service_path
        '''

        activity.Activity.__init__(self, handle, *args, **kwargs)

        self._sync_hid = None
        self._message_cbs = {}

        self._connection = None
        self._tube_conn = None

        self._pservice = presenceservice.get_instance()
        self._owner = self._pservice.get_owner()
        self._owner_id = str(self._owner.props.nick)

        self._service_path = kwargs.get('service_path',
            self._generate_service_path())
        self._dbus_object = None

        _logger.debug('Setting service name %s, service path %s', \
            IFACE, self._service_path)

        self._connect_to_ps()

    def get_shared_activity(self):
        '''Get shared_activity object; works for different API versions.'''
        try:
            return self.shared_activity
        except:
            return self._shared_activity

    def get_owner(self):
        '''Return buddy object of the owner.'''
        return self._owner

    def get_owner_id(self):
        '''Return id (nickname) of the owner.'''
        return self._owner_id

    def get_bus_name(self):
        '''
        Return the DBus bus name for the tube we're using, or None if there
        is no tube yet.
        '''
        if self._tube_conn is not None:
            return self._tube_conn.get_unique_name()
        else:
            return None

    def _generate_service_path(self):
        bundle_id = self.get_bundle_id()
        last = bundle_id.split('.')[-1]
        instance_id = self.get_id()
        return '/org/laptop/ShareableActivity/%s/%s' % (last, instance_id)

    def _connect_to_ps(self):
        '''
        Connect to the presence service.
        '''
        if self.get_shared_activity():
            self.connect('joined', self._sa_joined_cb)
            if self.get_shared():
                self._sa_joined_cb()
        else:
            self.connect('shared', self._sa_shared_cb)

    def _setup_shared_activity(self):
        '''
        Setup sharing stuff: get channels etc.
        '''

        sa = self.get_shared_activity()
        if sa is None:
            _logger.error('_setup_shared_activity(): no shared_activity yet!')
            return False

        self._connection = sa.telepathy_conn
        self._tubes_chan = sa.telepathy_tubes_chan
        self._text_chan = sa.telepathy_text_chan

        self._tubes_chan[telepathy.CHANNEL_TYPE_TUBES].connect_to_signal(
            'NewTube', self._new_tube_cb)

    def _sa_shared_cb(self, activity):
        self._setup_shared_activity()
        id = self._tubes_chan[telepathy.CHANNEL_TYPE_TUBES].OfferDBusTube(
            IFACE, {})

    def _sa_joined_cb(self, activity):
        """Callback for when we join an existing activity."""

        _logger.info('Joined existing activity')
        self._request_sync = True
        self._setup_shared_activity()

        self._tubes_chan[telepathy.CHANNEL_TYPE_TUBES].ListTubes( \
            reply_handler=self._list_tubes_reply_cb,
            error_handler=self._list_tubes_error_cb)

    def _list_tubes_reply_cb(self, tubes):
        """Callback for when requesting an existing tube"""
        _logger.debug('_list_tubes_reply_cb(): %r', tubes)
        for tube_info in tubes:
            self._new_tube_cb(*tube_info)

    def _list_tubes_error_cb(self, e):
        _logger.error('ListTubes() failed: %s', e)

    def _new_tube_cb(self, id, initiator, type, service, params, state):
        _logger.debug('New tube: ID=%d initator=%d type=%d service=%s '
                     'params=%r state=%d', id, initiator, type, service,
                     params, state)

        if (type == telepathy.TUBE_TYPE_DBUS and service == IFACE):
            if state == telepathy.TUBE_STATE_LOCAL_PENDING:
                self._tubes_chan[
                    telepathy.CHANNEL_TYPE_TUBES].AcceptDBusTube(id)

            self._tube_conn = SugarTubeConnection(self._connection,
                self._tubes_chan[telepathy.CHANNEL_TYPE_TUBES],
                id, group_iface=self._text_chan[
                    telepathy.CHANNEL_INTERFACE_GROUP])

            self._tube_conn.add_signal_receiver(self._send_message_cb,
                'SendMessage', sender_keyword='sender')

            self._dbus_object = ShareableObject(self._tube_conn, \
                    self._service_path)

    def buddy_joined(self, activity, buddy):
        '''
        Override to take action when a buddy joins.
        '''
        _logger.debug('Buddy joined: %s', buddy)

    def buddy_left(self, activity, buddy):
        '''
        Override to take action when a buddy left.
        '''
        _logger.debug('Buddy left: %s', buddy)

    def connect_message(self, msg, func):
        '''
        Connect function 'func' so that it's called when message <msg>
        is received. The function will receive keyword arguments sent
        with the message.
        '''
        self._message_cbs[msg] = func

    def message_received(self, msg, **kwargs):
        '''
        Override to take action when a message is received.
        This function will not be called for message handlers already
        registered with connect_message().
        '''
        _logger.debug('Received message: %s(%r)', msg, kwargs)

    def send_message(self, msg, **kwargs):
        '''
        Send a message to all connected buddies.
        '''
        if self._dbus_object is not None:
            _logger.debug('Sending message: %s(%r)', msg, kwargs)
            self._dbus_object.SendMessage(msg, kwargs)
        else:
            _logger.debug('Not shared, not sending message %s(%r)', \
                    msg, kwargs)

    def send_message_to(self, buddy, msg, **kwargs):
        '''
        Send a message to one particular buddy.
        '''
        if self._dbus_object is not None:
            _logger.debug('Sending message to %s: %s(%r)', buddy, msg, kwargs)
            #FIXME: convert to busname
            self._dbus_object.SendMessageTo(buddy, msg, kwargs)
        else:
            _logger.debug('Not shared, not sending message %s(%r) to %s', \
                msg, kwargs, buddy)

    def _dispatch_message(self, msg, kwargs):
        passkwargs = {}
        for k, v in kwargs.iteritems():
            passkwargs[str(k)] = v

        if msg in self._message_cbs:
            func = self._message_cbs[msg]
            func(**passkwargs)
        else:
            self.message_received(msg, **passkwargs)

    def _send_message_cb(self, msg, kwargs, sender=None):
        '''Callback to filter message signals.'''
        _logger.debug('Sender: %s, owner: %s, owner_id: %s, busname: %s', sender, \
                self.get_owner(), self.get_owner_id(), self.get_bus_name())
        if sender == self.get_bus_name():
            return
        kwargs['sender'] = sender
        self._dispatch_message(msg, kwargs)

    def _send_message_to_cb(self, to, msg, kwargs, sender=None):
        '''Callback to filter message signals.'''
        if to != self.get_bus_name():
            return
        kwargs['sender'] = sender
        kwargs['to'] = to
        self._dispatch_message(msg, kwargs)

    # FIXME: build a standard system to sync state from a single buddy
    def request_sync(self):
        if self._sync_hid is not None:
            return

        self._syncreq_buddy = 0
        self._sync_hid = gobject.timeout_add(2000, self._request_sync_cb)
        self._request_sync_cb()

    def _request_sync_cb(self):
        if self._syncreq_buddy <= len(self._connected_buddies):
            self._sync_hid = None
            return False

        self._syncreq_buddy += 1

