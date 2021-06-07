#!/usr/bin/python3
import argparse
import multiprocessing as mp
import os

def multiplo3(num):
    aprox=int(num-(num%3))
    return aprox

def header_size(fd):
    leer_header = os.read(fd, 50)
    leer_header = (leer_header.split(b'\n'))  # Crea una lista con los elementos del header separados por \n
    len_header = 0
    for i in range(len(leer_header)):
        if leer_header[i-1] == b'255':   # Compara el último elemento tomado por 'i'
            break
        len_header += (len(leer_header[i]))
        len_header += 1    # Representa los saltos de línea
    os.lseek(fd, 0, 0)
    return len_header

def escalar_valor(byte,escala):
    value = int.from_bytes(byte,'big')
    value = round(value*escala)
    if value > 255:
        value = 255
    return value.to_bytes(1,'big')

def generador_filtro(color,nombre_archivo,escala,header,conn,size):
    archivo_new= str(f'{color}_') + str(nombre_archivo)
    filtro = os.open(archivo_new,os.O_RDWR | os.O_CREAT)
    os.write(filtro,header)
    while True:
        chunk = conn.recv()
        pixels=list()
        for i in chunk:
            pixels.append(bytes([i]))
        if color == 'r':
            for i in range(0,len(pixels)-1,3):
                pixels[i] = escalar_valor(pixels[i],escala)
                pixels[i+1] = b'\x00'
                pixels[i+2] = b'\x00'
        elif color == 'g':
            for i in range(1,len(pixels),3):
                pixels[i-1] = b'\x00'
                pixels[i] = escalar_valor(pixels[i],escala)
                pixels[i+1] = b'\x00'
        elif color == 'b':
            for i in range(2,len(pixels),3):
                pixels[i-2] = b'\x00'
                pixels[i-1] = b'\x00'
                pixels[i] = escalar_valor(pixels[i],escala)
        pixels_mod = b''
        for i in pixels:
            pixels_mod = pixels_mod + i
        os.write(filtro,pixels_mod)
        if len(chunk) < size:
            break
    return (f'Se genero el filtro {color}')
            
         
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Tp1 - procesa ppm')
    parser.add_argument('-s', '--size',action="store", type= int, required=True, help="Bloque de lectura(Preferentemente un numero multiplo de 3)")
    parser.add_argument('-r', '--red_scale',action="store", type=float,default=1, required=False, help="Intensidad del color en el filtro rojo")
    parser.add_argument('-g', '--green_scale',action="store", type=float,default=1, required=False, help="Intensidad del color en el filtro verde")
    parser.add_argument('-b', '--blue_scale',action="store", type=float,default=1, required=False, help="Intensidad del color en el filtro azul")
    parser.add_argument('-f', '--file',action="store", required=True, type=str, help="Imagen que se usara")
    args =  parser.parse_args()
    
    foto = os.open(args.file,os.O_RDONLY)
    header = os.read(foto,header_size(foto))
    size = multiplo3(args.size)
    print(header)

    colores = ['r','g','b']
    escalas = [args.red_scale,args.green_scale,args.blue_scale]
    hijos = list()
    pipes = list()
    
    for i in range(3):
        parent_conn,child_conn = mp.Pipe()
        hijo = mp.Process(target=generador_filtro,args=(colores[i],args.file,escalas[i],header,child_conn,size))
        hijos.append(hijo)
        pipes.append(parent_conn)
    
    for i in hijos:
        i.start()
    
    while True:
        lectura = os.read(foto,size)
        for i in range(3):
            pipes[i].send(lectura)
        if len(lectura) < size and b'' in lectura:
            break
    os.close(foto)
    for i in pipes:
        i.close()