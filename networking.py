def recv_custom(socket):
    """
    receives message, parses size and type, reads data in chunks

    arguments:
    socket -- the connected socket
    """
    # Receive and parse size header
    try:
        header = socket.recv(5)
    except (ConnectionResetError, ConnectionAbortedError):
        return '', 0

    # To handle empty messsage from closed connections from trader after transaction is sent.
    if not header:
        return '', 0
    
    indicator = int(header[0])
    data_len = int.from_bytes(header[1:5], byteorder = "big")
    # Receive the rest of data based on size
    data = b""
    data_recv = 0
    while data_recv < data_len:
        chunk = socket.recv(min(data_len - data_recv, 1024))
        data += chunk
        data_recv += len(chunk)
    return data.decode(), indicator
    
def send_custom(socket, data, indicator):
    """
    sends data with custom 5-byte header
    data must be a string

    arguments:
    socket --  the connected socket
    data -- the data being sent
    indicator -- type of data
    """
    data = data.encode()
    data_len = len(data)
    indicator_bytes = indicator.to_bytes(1, byteorder="big")
    size_bytes = data_len.to_bytes(4, byteorder="big")
    socket.sendall(indicator_bytes + size_bytes + data)