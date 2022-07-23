'''
usage: python gen_diff.py -h
'''

from __future__ import print_function
import argparse
import time

from scipy.misc import imsave
from driving_models import *
from utils import *
import keras
import oss2


# import matplotlib.pyplot as plt
# sess = keras.backend.get_session()
# graph = tf.get_default_graph()


def deepXplore(seeds=100, transformation='light', weight_diff=1, weight_nc=0.1, step=10, grad_iterations=20,
               threshold=0):
    parser = argparse.ArgumentParser(
        description='Main function for difference-inducing input generation in Driving dataset')
    # parser.add_argument('transformation', help="realistic transformation type", choices=['light', 'occl', 'blackout'])
    # parser.add_argument('weight_diff', help="weight hyperparm to control differential behavior", type=float)
    # parser.add_argument('weight_nc', help="weight hyperparm to control neuron coverage", type=float)
    # parser.add_argument('step', help="step size of gradient descent", type=float)
    # parser.add_argument('seeds', help="number of seeds of input", type=int)
    # parser.add_argument('grad_iterations', help="number of iterations of gradient descent", type=int)
    # parser.add_argument('threshold', help="threshold for determining neuron activated", type=float)
    parser.add_argument('-t', '--target_model', help="target model that we want it predicts differently",
                        choices=[0, 1, 2], default=0, type=int)
    parser.add_argument('-sp', '--start_point', help="occlusion upper left corner coordinate", default=(0, 0),
                        type=tuple)
    parser.add_argument('-occl_size', '--occlusion_size', help="occlusion size", default=(50, 50), type=tuple)

    args = parser.parse_args()

    # aliyun OSS
    auth = oss2.Auth('yourAccessKeyId', 'yourAccessKeySecret')
    bucket = oss2.Bucket(auth, 'yourEndpoint', 'examplebucket')

    # input image dimensions
    img_rows, img_cols = 100, 100
    input_shape = (img_rows, img_cols, 3)

    # define input tensor as a placeholder
    input_tensor = Input(shape=input_shape)

    # load multiple models sharing same input tensor
    K.set_learning_phase(0)
    model1 = Dave_orig(input_tensor=input_tensor, load_weights=True)
    model2 = Dave_norminit(input_tensor=input_tensor, load_weights=True)
    model3 = Dave_dropout(input_tensor=input_tensor, load_weights=True)
    # init coverage table
    model_layer_dict1, model_layer_dict2, model_layer_dict3 = init_coverage_tables(model1, model2, model3)

    # ==============================================================================================
    # start gen inputs

    img_paths = image.list_pictures('./testing/center', ext='jpg')
    # print(img_paths)

    for _ in xrange(seeds):
        gen_img = preprocess_image(random.choice(img_paths))
        orig_img = gen_img.copy()
        # first check if input already induces differences
        # with sess.as_default():
        #     with graph.as_default():
        angle1, angle2, angle3 = model1.predict(gen_img)[0], model2.predict(gen_img)[0], \
                                 model3.predict(gen_img)[0]
        if angle_diverged(angle1, angle2, angle3):
            print(bcolors.OKGREEN + 'input already causes different outputs: {}, {}, {}'.format(angle1, angle2,
                                                                                                angle3) + bcolors.ENDC)

            update_coverage(gen_img, model1, model_layer_dict1, threshold)
            update_coverage(gen_img, model2, model_layer_dict2, threshold)
            update_coverage(gen_img, model3, model_layer_dict3, threshold)

            print(bcolors.OKGREEN + 'covered neurons percentage %d neurons %.3f, %d neurons %.3f, %d neurons %.3f'
                  % (len(model_layer_dict1), neuron_covered(model_layer_dict1)[2], len(model_layer_dict2),
                     neuron_covered(model_layer_dict2)[2], len(model_layer_dict3),
                     neuron_covered(model_layer_dict3)[2]) + bcolors.ENDC)
            averaged_nc = (neuron_covered(model_layer_dict1)[0] + neuron_covered(model_layer_dict2)[0] +
                           neuron_covered(model_layer_dict3)[0]) / float(
                neuron_covered(model_layer_dict1)[1] + neuron_covered(model_layer_dict2)[1] +
                neuron_covered(model_layer_dict3)[
                    1])
            print(bcolors.OKGREEN + 'averaged covered neurons %.3f' % averaged_nc + bcolors.ENDC)

            gen_img_deprocessed = draw_arrow(deprocess_image(gen_img), angle1, angle2, angle3)

            # save the result to disk
            imsave('./generated_inputs1/' + 'already_differ_' + str(angle1) + '_' + str(angle2) + '_' + str(
                angle3) + '.png',
                   gen_img_deprocessed)
            continue

        # if all turning angles roughly the same
        orig_angle1, orig_angle2, orig_angle3 = angle1, angle2, angle3
        layer_name1, index1 = neuron_to_cover(model_layer_dict1)
        layer_name2, index2 = neuron_to_cover(model_layer_dict2)
        layer_name3, index3 = neuron_to_cover(model_layer_dict3)

        # construct joint loss function
        if args.target_model == 0:
            loss1 = -weight_diff * K.mean(model1.get_layer('before_prediction').output[..., 0])
            loss2 = K.mean(model2.get_layer('before_prediction').output[..., 0])
            loss3 = K.mean(model3.get_layer('before_prediction').output[..., 0])
        elif args.target_model == 1:
            loss1 = K.mean(model1.get_layer('before_prediction').output[..., 0])
            loss2 = -weight_diff * K.mean(model2.get_layer('before_prediction').output[..., 0])
            loss3 = K.mean(model3.get_layer('before_prediction').output[..., 0])
        elif args.target_model == 2:
            loss1 = K.mean(model1.get_layer('before_prediction').output[..., 0])
            loss2 = K.mean(model2.get_layer('before_prediction').output[..., 0])
            loss3 = -weight_diff * K.mean(model3.get_layer('before_prediction').output[..., 0])
        loss1_neuron = K.mean(model1.get_layer(layer_name1).output[..., index1])
        loss2_neuron = K.mean(model2.get_layer(layer_name2).output[..., index2])
        loss3_neuron = K.mean(model3.get_layer(layer_name3).output[..., index3])
        layer_output = (loss1 + loss2 + loss3) + weight_nc * (loss1_neuron + loss2_neuron + loss3_neuron)

        # for adversarial image generation
        final_loss = K.mean(layer_output)

        # we compute the gradient of the input picture wrt this loss
        grads = normalize(K.gradients(final_loss, input_tensor)[0])

        # this function returns the loss and grads given the input picture
        iterate = K.function([input_tensor], [loss1, loss2, loss3, loss1_neuron, loss2_neuron, loss3_neuron, grads])

        # we run gradient ascent for 20 steps
        for iters in xrange(grad_iterations):
            loss_value1, loss_value2, loss_value3, loss_neuron1, loss_neuron2, loss_neuron3, grads_value = iterate(
                [gen_img])
            if transformation == 'light':
                grads_value = constraint_light(grads_value)  # constraint the gradients value
            elif transformation == 'occl':
                grads_value = constraint_occl(grads_value, args.start_point,
                                              args.occlusion_size)  # constraint the gradients value
            elif transformation == 'blackout':
                grads_value = constraint_black(grads_value)  # constraint the gradients value

            gen_img += grads_value * step
            # with sess.as_default():
            #     with graph.as_default():
            angle1, angle2, angle3 = model1.predict(gen_img)[0], model2.predict(gen_img)[0], \
                                     model3.predict(gen_img)[0]

            if angle_diverged(angle1, angle2, angle3):
                update_coverage(gen_img, model1, model_layer_dict1, threshold)
                update_coverage(gen_img, model2, model_layer_dict2, threshold)
                update_coverage(gen_img, model3, model_layer_dict3, threshold)

                print(bcolors.OKGREEN + 'covered neurons percentage %d neurons %.3f, %d neurons %.3f, %d neurons %.3f'
                      % (len(model_layer_dict1), neuron_covered(model_layer_dict1)[2], len(model_layer_dict2),
                         neuron_covered(model_layer_dict2)[2], len(model_layer_dict3),
                         neuron_covered(model_layer_dict3)[2]) + bcolors.ENDC)
                averaged_nc = (neuron_covered(model_layer_dict1)[0] + neuron_covered(model_layer_dict2)[0] +
                               neuron_covered(model_layer_dict3)[0]) / float(
                    neuron_covered(model_layer_dict1)[1] + neuron_covered(model_layer_dict2)[1] +
                    neuron_covered(model_layer_dict3)[
                        1])
                print(bcolors.OKGREEN + 'averaged covered neurons %.3f' % averaged_nc + bcolors.ENDC)

                gen_img_deprocessed = draw_arrow(deprocess_image(gen_img), angle1, angle2, angle3)
                orig_img_deprocessed = draw_arrow(deprocess_image(orig_img), orig_angle1, orig_angle2, orig_angle3)

                # save the result to disk
                gen_img = (transformation + '_' + str(angle1) + '_' + str(angle2) \
                           + '_' + str(angle3) + '_' + str(int(time.time())) + '.png')
                gen_img_path = './generated_inputs1/' + gen_img
                imsave(gen_img_path, gen_img_deprocessed)

                orig_img = (transformation + '_' + str(angle1) + '_' + str(angle2) + '_' \
                            + str(angle3) + '_orig' + '_' + str(int(time.time())) + '.png')
                orig_img_path = './generated_inputs1/' + orig_img
                imsave(orig_img_path, orig_img_deprocessed)

                # upload image
                bucket.put_object_from_file(gen_img, gen_img_path)
                bucket.put_object_from_file(orig_img, orig_img_path)
                break


if __name__ == '__main__':
    deepXplore()
