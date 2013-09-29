$(function() {
	var alarm_map = { frequency: 'al-freq', single: 'al-single' };
	$('#al-type').change(function(evt) {
		var set = $(this).parents('fieldset').first();
		set.children('fieldset').hide();
		set.find('label[for=' + alarm_map[$(this).val()] + ']').
			parents('fieldset').first().show();
	});

	var action_map = { randplaylist: 'act-randplaylist' };
	$('#act-type').change(function(evt) {
		var set = $(this).parents('fieldset').first();
		set.children('fieldset').hide();
		set.find('label[for=' + action_map[$(this).val()] + ']').
			parents('fieldset').first().show();
	});
});

