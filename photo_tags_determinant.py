import cv2
import numpy

def determine_photo_tags(image_url):
    #Файлы для настройки сети
    cfg_path = 'NeuralNetwork_files/yolov4-tiny.cfg'
    weights_path = 'NeuralNetwork_files/yolov4-tiny.weights'
    class_path = 'NeuralNetwork_files/coco.names.txt'

    tags = []

    net = cv2.dnn.readNetFromDarknet(cfg_path, weights_path)
    layer_names = net.getLayerNames()
    out_layers_indexes = net.getUnconnectedOutLayers()

    out_layers = [layer_names[index - 1] for index in out_layers_indexes]

    with open(class_path) as file:
        classes = file.read().split('\n')

    unique_tags = ['cat', 'bird', 'dog']
    other_tags = ['bear', 'teddy bear', 'giraffe', 'zebra', 'bear', 'elephant', 'cow', 'sheep', 'horse']

    image = cv2.imread(image_url)

    blob = cv2.dnn.blobFromImage(image, 1/255, (608, 608), (0,0,0), swapRB =True, crop = False)

    net.setInput(blob)
    outs = net.forward(out_layers)

    class_indexes = []

    for out in outs:
        for object in out:
            scores = object[5:]
            class_index = numpy.argmax(scores)
            class_score = scores[class_index]

            if class_score > 0:
                class_indexes.append(class_index)

    for i in class_indexes:
        if classes[i] in unique_tags:
            tags.append(f'{classes[i]}s')

        elif classes[i] == 'mouse':
            tags.append('hamsters')

        elif classes[i] in other_tags:
            tags.append('others')

        else:
            pass

    tags = list(set(tags))

    cv2.destroyAllWindows()

    return tags
