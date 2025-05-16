from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from google.protobuf import descriptor_pool as _descriptor_pool

DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'''
    syntax = "proto3";
    package com.upstox.marketdata;
    
    message FeedResponse {
        string type = 1;
        repeated Feed feeds = 2;
    }
    
    message Feed {
        string symbol = 1;
        double ltp = 2;
        double close = 3;
        int64 ltq = 4;
        string exchange = 5;
        string tradingSymbol = 6;
        string instrumentToken = 7;
        double high = 8;
        double low = 9;
        double open = 10;
        int64 volume = 11;
        double bid = 12;
        double ask = 13;
        int64 bidSize = 14;
        int64 askSize = 15;
        string timestamp = 16;
    }
''')

_FEEDRESPONSE = DESCRIPTOR.message_types_by_name['FeedResponse']
_FEED = DESCRIPTOR.message_types_by_name['Feed']

class FeedResponse(_message.Message):
    __slots__ = ["type", "feeds"]
    TYPE_FIELD_NUMBER = 1
    FEEDS_FIELD_NUMBER = 2
    
    def __init__(self, **kwargs):
        super(FeedResponse, self).__init__(**kwargs)
        self.type = ""
        self.feeds = []

class Feed(_message.Message):
    __slots__ = ["symbol", "ltp", "close", "ltq", "exchange", "tradingSymbol", 
                 "instrumentToken", "high", "low", "open", "volume", "bid", "ask",
                 "bidSize", "askSize", "timestamp"]
    
    def __init__(self, **kwargs):
        super(Feed, self).__init__(**kwargs)
        self.symbol = ""
        self.ltp = 0.0
        self.close = 0.0
        self.ltq = 0
        self.exchange = ""
        self.tradingSymbol = ""
        self.instrumentToken = ""
        self.high = 0.0
        self.low = 0.0
        self.open = 0.0
        self.volume = 0
        self.bid = 0.0
        self.ask = 0.0
        self.bidSize = 0
        self.askSize = 0
        self.timestamp = ""