from PythonAPI.prepare_data import prepare_dataset
import deeplab
from PythonAPI.pycocotools.coco import COCO

def main(train_type='Resnet', restore=False, maxiter=10, test=False):
	train_annFile = './annotations/instances_train2017.json'
	val_annFile = './annotations/instances_val2017.json'

	train_coco = COCO(train_annFile)
	val_coco = COCO(val_annFile)
	train_dataset = prepare_dataset(train_coco)
	val_dataset = prepare_dataset(val_coco)

	res_train_iter = train_dataset.res_dataset.make_initializable_iterator()
	deep_train_iter = train_dataset.deep_dataset.make_initializable_iterator()
	res_val_iter = val_dataset.res_dataset.make_initializable_iterator()
	deep_val_iter = val_dataset.deep_dataset.make_initializable_iterator()
	next_res_train = res_train_iter.get_next()
	next_deep_train = deep_train_iter.get_next()
	next_res_val = res_val_iter.get_next()
	next_deep_val = deep_val_iter.get_next()

	#_imgs = tf.placeholder(tf.float32, [batch_size, None, None, 3])
	#_labels = tf.placeholder(tf.float32, [batch_size, num_classes])
	#_gt = tf.placeholder(tf.float32, [batch_size, None, None, num_classes])
	training = tf.placeholder(tf.bool)
	res_end = tf.placeholder(tf.bool)

	if res_end:
		if training:
			_imgs, _labels = next_res_train
		else:
			_imgs, _labels = next_res_val
	else:
		if training:
			_imgs, _gt = next_deep_train
		else:
			_imgs, _gt = next_deep_val

	_deeplab = deeplab.deeplab_v3_plus(_imgs, [128, 64], [48, num_classes], num_classes)
	res_out = _deeplab.get_dense()
	res_loss = tf.nn.softmax_cross_entropy_with_logits(labels=_labels, logits=res_out, name='res_loss')
	res_mean_loss = tf.nn.reduce_mean(res_loss)
	res_op = tf.train.AdamOptimizer().minimize(res_loss)

	pred_out = _deeplab.get_pred()
	pred_loss = tf.nn.softmax_cross_entropy_with_logits(labels=tf.reshape(_gt, [-1, num_classes]), logits=tf.reshape(pred_out, [-1, num_classes]), name='pred_loss')
	pred_mean_loss = tf.nn.reduce_mean(pred_loss)
	pred_op = tf.train.AdamOptimizer().minimize(pred_loss)

	saver = tf.train.Saver()
	with tf.Session() as sess:
		if restore:
			saver.restore(sess, "./model/model.ckpt")
			print('restored')
		else:
			sess.run(tf.global_variable_initializer())
			print('initial done')

		if train_type == 'Resnet':
			for i in list(range(maxiter)):
				cnt = 0
				total_loss = 0.0
				sess.run(res_train_iter.initializer)
				while True:
					try:
						_, _loss = sess.run([res_op, res_mean_loss], feed_dict={training: True, res_end: True})
						total_loss += _loss
						cnt += 1
						if cnt % 25 == 0:
							print(cnt * 16, total_loss / 25)
							total_loss = 0.0
					except tf.errors.OutOfRangeError:
						break
				print('epoc %d done' % (i + 1))

				cnt = 0
				total_loss = 0.0
				sess.run(res_val_iter.initializer)
				while True:
					try:
						_, _loss = sess.run([res_op, res_mean_loss], feed_dict={training: False, res_end: True})
						total_loss += _loss
						cnt += 1
						if cnt % 25 == 0:
							print(cnt * 16, total_loss / 25)
							total_loss = 0.0
					except tf.errors.OutOfRangeError:
						break

				saver.save(sess, "./model/model.ckpt")
				saver.save(sess, "./model/model_%d.ckpt" % i)
				print('model saved')
		elif train_type == 'Deeplab':
		else:
			pass

if __name__ == '__main__':
	main('Resnet')